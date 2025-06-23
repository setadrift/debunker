import NetworkGraph from '../components/NetworkGraph';

export default function GraphPage() {
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Source Network</h1>
      <NetworkGraph />
    </div>
  );
} 