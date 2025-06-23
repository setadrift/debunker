import { useEffect, useState } from 'react';
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-expect-error esm
import ForceGraph2D from 'react-force-graph-2d';

interface GraphNode {
  id: string;
  platform: string;
  engagement: number;
}

interface Link {
  source: string;
  target: string;
}

interface GraphData {
  nodes: GraphNode[];
  links: Link[];
}

export default function NetworkGraph() {
  const [data, setData] = useState<GraphData>({ nodes: [], links: [] });

  useEffect(() => {
    fetch('http://localhost:8000/api/graph')
      .then((res) => res.json())
      .then(setData)
      .catch((err) => console.error('Failed to load graph', err));
  }, []);

  return (
    <div className="w-full h-screen">
      <ForceGraph2D
        graphData={data}
        nodeLabel={(node: GraphNode) => `${(node as GraphNode).platform}\nEngagement: ${(node as GraphNode).engagement}`}
        nodeAutoColorBy="platform"
        linkDirectionalParticles={2}
        linkDirectionalParticleSpeed={0.005}
      />
    </div>
  );
} 