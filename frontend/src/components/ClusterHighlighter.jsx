import { useMemo } from 'react'
import { Html } from '@react-three/drei'
import * as THREE from 'three'

export function ClusterHighlighter({ analysis, onSelect }) {
    if (!analysis || !analysis.clusters) return null

    return (
        <group>
            {analysis.clusters.map((cluster) => (
                <group key={cluster.id} position={cluster.pos}>
                    {/* Cluster Core Marker */}
                    <mesh onClick={(e) => { e.stopPropagation(); onSelect(cluster); }}>
                        <sphereGeometry args={[5, 16, 16]} />
                        <meshBasicMaterial color="hotpink" wireframe transparent opacity={0.3} />
                    </mesh>

                    {/* Label */}
                    <Html distanceFactor={100}>
                        <div style={{ color: 'hotpink', background: 'rgba(0,0,0,0.5)', padding: '2px 5px', borderRadius: '4px' }}>
                            Cluster {cluster.id}
                        </div>
                    </Html>

                    {/* Velocity Vector (scaled) */}
                    <arrowHelper
                        args={[
                            new THREE.Vector3(...cluster.vel).normalize(),
                            new THREE.Vector3(0, 0, 0),
                            50, // Length
                            'cyan'
                        ]}
                    />

                    {/* Tidal Tails */}
                    {cluster.tail_members && cluster.tail_members.length > 0 && (
                        // We can't easily render individual tail stars here without their positions.
                        // But we can visualize the "concept" or if we passed full star data we could.
                        // For now, let's just add a label saying "Tails detected"
                        <Html position={[0, -10, 0]} distanceFactor={100}>
                            <div style={{ color: 'orange', fontSize: '10px' }}>
                                {cluster.tail_members.length} tail candidates
                            </div>
                        </Html>
                    )}
                </group>
            ))}

            {/* Runaways */}
            {/* We could render lines for runaways if we had their positions. 
          The analysis.json only has IDs. We need to map them. 
          For now, let's skip rendering runaways here or pass full star data.
      */}
        </group>
    )
}
