import pandas as pd
import numpy as np
import hdbscan
from sklearn.preprocessing import StandardScaler
import json
import os

def analyze_clusters():
    print("Loading data...")
    df = pd.read_csv('backend/stars_raw.csv')
    
    # 1. Preprocessing
    # We need to convert astrometric data to Cartesian position and velocity
    # Position (x,y,z) was already computed in fetch_data.py but let's recompute to be safe or just use what we have if we saved it.
    # The CSV has ra, dec, parallax, pmra, pmdec, radial_velocity.
    # Let's compute full 6D coordinates.
    
    # Constants
    k = 4.74047 # km/s * yr / (pc * mas) ? No, 4.74047 km/s / (mas/yr * kpc) ?
    # v_tan = 4.74 * pm / parallax (if pm in mas/yr, parallax in mas, v in km/s)
    
    # Distance in pc
    df['dist_pc'] = 1000.0 / df['parallax']
    
    # Position (Galactic or Equatorial Cartesian)
    # Let's stick to Equatorial Cartesian for simplicity as used in fetch_data
    ra_rad = np.deg2rad(df['ra'])
    dec_rad = np.deg2rad(df['dec'])
    
    df['x'] = df['dist_pc'] * np.cos(dec_rad) * np.cos(ra_rad)
    df['y'] = df['dist_pc'] * np.cos(dec_rad) * np.sin(ra_rad)
    df['z'] = df['dist_pc'] * np.sin(dec_rad)
    
    # Velocity
    # Proper motion components in km/s
    # pm_ra is usually pm_ra * cos(dec) in Gaia? No, Gaia provides pmra = mu_alpha * cos(delta).
    # So tangential velocities:
    k = 4.74047
    v_ra = k * df['pmra'] / df['parallax']
    v_dec = k * df['pmdec'] / df['parallax']
    v_rad = df['radial_velocity']
    
    # We need to rotate these into Cartesian v_x, v_y, v_z
    # This transformation is complex. For clustering, we can cluster in (x,y,z, pmra, pmdec, parallax) space 
    # or (x,y,z, v_ra, v_dec, v_rad) space.
    # Let's use the 5D astrometric parameters + radial velocity scaled appropriately.
    # Or just use positions and velocities.
    
    # Simplified approach for demo: Cluster on (x, y, z, v_ra, v_dec, v_rad)
    # Note: v_ra and v_dec are along spherical directions. This is not ideal for large volumes but okay for local.
    # Better: Cluster on (x, y, z, pmra, pmdec) to find comoving groups.
    
    print("Clustering...")
    # Scale features
    # We want to weight position and velocity.
    # 1 pc difference != 1 km/s difference.
    # Let's normalize.
    features = df[['x', 'y', 'z', 'pmra', 'pmdec', 'radial_velocity']].copy()
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    # HDBSCAN Tuning
    # min_cluster_size: Smallest size to consider a cluster. Increased to 50 to avoid tiny noise groups.
    # min_samples: How conservative the clustering is. Increased to 15 to reduce noise.
    # cluster_selection_method: 'leaf' tends to produce more fine-grained clusters than 'eom'.
    clusterer = hdbscan.HDBSCAN(min_cluster_size=50, min_samples=15, cluster_selection_method='leaf', metric='euclidean')
    labels = clusterer.fit_predict(features_scaled)
    
    df['cluster_id'] = labels
    
    # 2. Identify Tidal Tails & Runaways
    # For each cluster, calculate core properties
    clusters = []
    tails = []
    runaways = []
    
    unique_labels = set(labels)
    if -1 in unique_labels:
        unique_labels.remove(-1)
        
    print(f"Found {len(unique_labels)} clusters.")
    
    for label in unique_labels:
        cluster_members = df[df['cluster_id'] == label]
        
        # Calculate centroid and velocity mean
        center_pos = cluster_members[['x', 'y', 'z']].mean().values
        center_vel = cluster_members[['pmra', 'pmdec', 'radial_velocity']].mean().values
        
        # Calculate dispersion (std dev)
        std_pos = cluster_members[['x', 'y', 'z']].std().values
        std_vel = cluster_members[['pmra', 'pmdec', 'radial_velocity']].std().values
        
        # Define "Tail" candidates:
        # Stars NOT in the cluster (label -1) but close in phase space.
        # specifically: close in velocity, but spatially outside the core.
        
        noise_points = df[df['cluster_id'] == -1]
        
        # Velocity matching:
        # v_star - v_cluster_mean < 2 * std_vel (in 3D velocity space)
        # For simplicity, let's use the scaled features or just raw velocity difference.
        # Let's use raw velocity difference.
        
        # Vectorized check
        # Velocity difference
        dv_ra = noise_points['pmra'] - center_vel[0]
        dv_dec = noise_points['pmdec'] - center_vel[1]
        dv_rad = noise_points['radial_velocity'] - center_vel[2]
        
        # Normalized by dispersion (avoid division by zero)
        sig_ra = max(std_vel[0], 0.1)
        sig_dec = max(std_vel[1], 0.1)
        sig_rad = max(std_vel[2], 0.1)
        
        # Chi-squared like distance in velocity
        vel_dist_sq = (dv_ra/sig_ra)**2 + (dv_dec/sig_dec)**2 + (dv_rad/sig_rad)**2
        
        # Candidates: velocity match < 2 sigma (dist_sq < 4)
        candidates = noise_points[vel_dist_sq < 9.0] # 3 sigma for looser tail detection
        
        # Spatial check: Must be somewhat near? 
        # Tidal tails can be long. Let's limit to 100pc from center to avoid random matches across the sky.
        dx = candidates['x'] - center_pos[0]
        dy = candidates['y'] - center_pos[1]
        dz = candidates['z'] - center_pos[2]
        dist_sq = dx**2 + dy**2 + dz**2
        
        tail_members = candidates[dist_sq < 10000] # 100 pc radius
        
        tail_ids = tail_members['source_id'].tolist()
        tails.append({
            'cluster_id': int(label),
            'member_ids': tail_ids
        })
        
        clusters.append({
            'id': int(label),
            'count': int(len(cluster_members)),
            'pos': center_pos.tolist(),
            'vel': center_vel.tolist(),
            'std_pos': std_pos.tolist(),
            'std_vel': std_vel.tolist(),
            'members': cluster_members['source_id'].tolist(),
            'tail_members': tail_ids
        })

    # 3. Find Runaways (High velocity relative to local mean)
    # Calculate local velocity field? Or just high total velocity?
    # Let's find stars with total velocity > 100 km/s (just as an example of high velocity)
    # v_tot = sqrt(v_ra^2 + v_dec^2 + v_rad^2)
    df['v_tot'] = np.sqrt(v_ra**2 + v_dec**2 + v_rad**2)
    high_vel_stars = df[df['v_tot'] > 100] # Arbitrary threshold for "runaway" in this context
    
    # Save results
    output_data = {
        'clusters': clusters,
        'runaways': high_vel_stars['source_id'].tolist()
    }
    
    with open('frontend/public/analysis.json', 'w') as f:
        json.dump(output_data, f)
        
    # Update stars.json with cluster IDs?
    # It's better to have a separate file or merge.
    # Let's merge cluster_id into stars.json
    
    # Read existing stars.json
    # Actually, we can just overwrite it with the new dataframe that has cluster_id
    # But fetch_data.py saved a subset.
    
    # Let's save a new stars_analyzed.json
    out_df = df[['source_id', 'x', 'y', 'z', 'bp_rp', 'phot_g_mean_mag', 'pmra', 'pmdec', 'radial_velocity', 'cluster_id', 'v_tot']]
    out_df.to_json('frontend/public/stars.json', orient='records')
    print("Saved analyzed data to frontend/public/stars.json")

if __name__ == "__main__":
    analyze_clusters()
