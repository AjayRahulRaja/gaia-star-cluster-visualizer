import { useState, useEffect, Suspense } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Stars as BackgroundStars } from '@react-three/drei'
import { StarField } from './components/StarField'
import { ClusterHighlighter } from './components/ClusterHighlighter'
import { HRDiagram } from './components/HRDiagram'

function App() {
    const [stars, setStars] = useState([])
    const [analysis, setAnalysis] = useState(null)
    const [loading, setLoading] = useState(true)
    const [selectedCluster, setSelectedCluster] = useState(null)

    useEffect(() => {
        Promise.all([
            fetch('/stars.json').then(res => res.json()),
            fetch('/analysis.json').then(res => res.json())
        ]).then(([starsData, analysisData]) => {
            setStars(starsData)
            setAnalysis(analysisData)
            setLoading(false)
        }).catch(err => {
            console.error("Failed to load data", err)
            setLoading(false)
        })
    }, [])

    if (loading) return <div style={{ color: 'white', padding: '20px' }}>Loading Gaia Data...</div>

    return (
        <div style={{ width: '100vw', height: '100vh', background: '#000' }}>
            <Canvas camera={{ position: [0, 100, 300], fov: 60, far: 2000 }}>
                <color attach="background" args={['#050505']} />

                <ambientLight intensity={0.5} />
                <pointLight position={[10, 10, 10]} />

                <Suspense fallback={null}>
                    <StarField stars={stars} />
                    <ClusterHighlighter
                        analysis={analysis}
                        onSelect={setSelectedCluster}
                    />
                    <BackgroundStars radius={1000} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
                </Suspense>

                <OrbitControls autoRotate autoRotateSpeed={0.5} />
            </Canvas>

            <div style={{ position: 'absolute', top: 20, left: 20, color: 'white', pointerEvents: 'none' }}>
                <h1>Gaia Star Cluster Visualizer</h1>
                <p>Stars: {stars.length}</p>
                <p>Clusters Found: {analysis?.clusters?.length || 0}</p>
                <p>Distance Limit: 650 pc</p>
            </div>

            <div style={{ position: 'absolute', bottom: 20, right: 20, pointerEvents: 'auto' }}>
                <HRDiagram stars={stars} selectedCluster={selectedCluster} />
            </div>
        </div>
    )
}

export default App
