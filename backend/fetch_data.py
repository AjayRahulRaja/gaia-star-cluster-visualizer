import os
import time
import numpy as np
import pandas as pd
from astroquery.gaia import Gaia
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

def fetch_gaia_data(limit_pc=650, max_stars=50000):
    """
    Fetch stars from Gaia DR3 within a certain distance.
    """
    print(f"Fetching Gaia DR3 data within {limit_pc} pc...")
    
    # Parallax limit: p > 1000 / limit_pc (in mas)
    parallax_limit = 1000.0 / limit_pc
    
    query = f"""
    SELECT TOP {max_stars}
        source_id, ra, dec, parallax, pmra, pmdec, radial_velocity,
        phot_g_mean_mag, bp_rp,
        x, y, z,
        v_x, v_y, v_z
    FROM gaiadr3.gaia_source
    WHERE parallax > {parallax_limit}
      AND phot_g_mean_mag < 13
      AND radial_velocity IS NOT NULL
    """
    
    # Note: Gaia archive has geometric distances in separate tables usually, 
    # but for this demo we use 1/parallax as approximation or use pre-computed x,y,z if available.
    # Actually, gaiadr3.gaia_source does NOT have x,y,z columns directly.
    # We need to compute them or join with another table.
    # For simplicity, we will fetch spherical coordinates and convert in Python.
    
    query = f"""
    SELECT TOP {max_stars}
        source_id, ra, dec, parallax, pmra, pmdec, radial_velocity,
        phot_g_mean_mag, bp_rp
    FROM gaiadr3.gaia_source
    WHERE parallax > {parallax_limit}
      AND phot_g_mean_mag < 13
      AND radial_velocity IS NOT NULL
    """
    
    job = Gaia.launch_job_async(query)
    r = job.get_results()
    
    df = r.to_pandas()
    print(f"Fetched {len(df)} stars.")
    
    # Calculate 3D coordinates (Cartesian)
    # Distance r in parsecs = 1000 / parallax (mas)
    df['dist_pc'] = 1000.0 / df['parallax']
    
    # Convert RA/Dec/Dist to Cartesian
    # RA, Dec are in degrees. Convert to radians.
    ra_rad = np.deg2rad(df['ra'])
    dec_rad = np.deg2rad(df['dec'])
    
    df['x'] = df['dist_pc'] * np.cos(dec_rad) * np.cos(ra_rad)
    df['y'] = df['dist_pc'] * np.cos(dec_rad) * np.sin(ra_rad)
    df['z'] = df['dist_pc'] * np.sin(dec_rad)
    
    # Save to JSON
    output_file = 'frontend/public/stars.json'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Select columns for frontend
    out_df = df[['source_id', 'x', 'y', 'z', 'bp_rp', 'phot_g_mean_mag', 'pmra', 'pmdec', 'radial_velocity']]
    out_df.to_json(output_file, orient='records')
    print(f"Saved data to {output_file}")
    
    # Save full data for analysis
    df.to_csv('backend/stars_raw.csv', index=False)
    print("Saved raw data to backend/stars_raw.csv")

if __name__ == "__main__":
    fetch_gaia_data()
