import { useRef, useMemo, useEffect, useState } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'

export function StarField({ stars }) {
    const pointsRef = useRef()

    const { positions, colors, sizes } = useMemo(() => {
        const positions = new Float32Array(stars.length * 3)
        const colors = new Float32Array(stars.length * 3)
        const sizes = new Float32Array(stars.length)

        const colorObj = new THREE.Color()

        stars.forEach((star, i) => {
            positions[i * 3] = star.x
            positions[i * 3 + 1] = star.y
            positions[i * 3 + 2] = star.z

            // Color based on bp_rp (approximate)
            // Low bp_rp (blue) -> High bp_rp (red)
            // Range roughly -0.5 to 3.0
            const bp_rp = star.bp_rp || 1.0
            let r, g, b

            if (bp_rp < 0.5) { colorObj.setHSL(0.6, 1, 0.8); } // Blue
            else if (bp_rp < 1.0) { colorObj.setHSL(0.1, 1, 0.9); } // White/Yellow
            else { colorObj.setHSL(0.05, 1, 0.6); } // Red

            colors[i * 3] = colorObj.r
            colors[i * 3 + 1] = colorObj.g
            colors[i * 3 + 2] = colorObj.b

            // Size based on magnitude (smaller mag = brighter = bigger)
            // Mag range ~ -2 to 13
            // Size = 1.0 / (mag + 3) * scale
            sizes[i] = Math.max(0.1, (15 - star.phot_g_mean_mag) * 0.5)
        })

        return { positions, colors, sizes }
    }, [stars])

    return (
        <points ref={pointsRef}>
            <bufferGeometry>
                <bufferAttribute
                    attach="attributes-position"
                    count={positions.length / 3}
                    array={positions}
                    itemSize={3}
                />
                <bufferAttribute
                    attach="attributes-color"
                    count={colors.length / 3}
                    array={colors}
                    itemSize={3}
                />
                <bufferAttribute
                    attach="attributes-size" // Custom attribute for shader if needed, or use size in material
                    count={sizes.length}
                    array={sizes}
                    itemSize={1}
                />
            </bufferGeometry>
            <pointsMaterial
                size={0.5}
                vertexColors
                sizeAttenuation
                depthWrite={false}
                transparent
                opacity={0.8}
            />
        </points>
    )
}
