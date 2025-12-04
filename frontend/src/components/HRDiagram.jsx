import { useMemo } from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export function HRDiagram({ stars, selectedCluster, width = 300, height = 300 }) {
    const data = useMemo(() => {
        if (!selectedCluster) return [];

        // Filter stars belonging to the cluster
        const clusterStars = stars.filter(s => selectedCluster.members.includes(s.source_id));

        return clusterStars.map(s => ({
            x: s.bp_rp, // Color (Temperature)
            y: s.phot_g_mean_mag, // Absolute Magnitude (approx, using apparent for now as distance is similar)
            // Ideally calculate Absolute Mag M = m - 5 * log10(d/10)
            // d = 1000/parallax
            // M = m + 5 - 5 * log10(1000/parallax)
            abs_mag: s.phot_g_mean_mag + 5 - 5 * Math.log10(1000 / (s.parallax || 0.001)),
            id: s.source_id
        })).filter(s => s.x != null && s.y != null);
    }, [stars, selectedCluster]);

    if (!selectedCluster) {
        return (
            <div style={{ width, height, background: 'rgba(0,0,0,0.8)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid #333' }}>
                <p>Select a cluster to view HR Diagram</p>
            </div>
        );
    }

    const downloadClusterData = () => {
        if (!selectedCluster || !data.length) return;

        const csvContent = "data:text/csv;charset=utf-8,"
            + "source_id,bp_rp,abs_mag\n"
            + data.map(row => `${row.id},${row.x},${row.abs_mag}`).join("\n"); // Changed row.y to row.abs_mag as per YAxis dataKey

        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `cluster_${selectedCluster.id}_data.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    return (
        <div style={{ width, height, background: 'rgba(0,0,0,0.8)', padding: '10px', border: '1px solid #333', borderRadius: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <h3 style={{ margin: 0, fontSize: '14px', color: '#ccc' }}>Cluster {selectedCluster.id} HR Diagram</h3>
                <button onClick={downloadClusterData} style={{ fontSize: '10px', padding: '2px 5px', cursor: 'pointer' }}>Export CSV</button>
            </div>
            <ResponsiveContainer width="100%" height="85%">
                <ScatterChart margin={{ top: 10, right: 10, bottom: 20, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                    <XAxis
                        type="number"
                        dataKey="x"
                        name="Color (Bp-Rp)"
                        stroke="#888"
                        label={{ value: 'Blue <---> Red', position: 'bottom', fill: '#888', fontSize: 10 }}
                        domain={['auto', 'auto']}
                    />
                    <YAxis
                        type="number"
                        dataKey="abs_mag"
                        name="Abs Magnitude"
                        stroke="#888"
                        reversed={true} // Magnitude is brighter when lower
                        label={{ value: 'Brightness', angle: -90, position: 'insideLeft', fill: '#888', fontSize: 10 }}
                        domain={['auto', 'auto']}
                    />
                    <Tooltip
                        cursor={{ strokeDasharray: '3 3' }}
                        contentStyle={{ backgroundColor: '#333', border: 'none', color: '#fff' }}
                    />
                    <Scatter name="Stars" data={data} fill="#8884d8" shape="circle">
                        {data.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.x < 0.8 ? '#aaddff' : entry.x > 1.5 ? '#ffaa88' : '#ffffaa'} />
                        ))}
                    </Scatter>
                </ScatterChart>
            </ResponsiveContainer>
        </div>
    );
}
