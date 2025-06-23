import { useEffect, useState } from "react";
import Card from "../components/Card";
import Dashboard from "../components/Dashboard";

type Narrative = {
  id: number;
  summary: string;
  source_count: number;
  last_seen: string;
  first_seen: string;
};

export default function Home() {
  const [narratives, setNarratives] = useState<Narrative[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'recent' | 'sources'>('recent');

  useEffect(() => {
    const fetchNarratives = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await fetch("http://localhost:8000/api/narratives");
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        setNarratives(data);
      } catch (error) {
        console.error('Failed to fetch narratives:', error);
        setError(error instanceof Error ? error.message : 'Failed to load narratives');
      } finally {
        setLoading(false);
      }
    };

    fetchNarratives();
  }, []);

  const sortedNarratives = [...narratives].sort((a, b) => {
    if (sortBy === 'recent') {
      return new Date(b.last_seen).getTime() - new Date(a.last_seen).getTime();
    } else {
      return b.source_count - a.source_count;
    }
  });

  if (loading) {
    return (
      <div className="space-y-8">
        {/* Hero Section Loading */}
        <div className="text-center py-12">
          <div className="skeleton h-10 mx-auto mb-4 rounded" style={{ width: '66.666667%' }}></div>
          <div className="skeleton h-6 mx-auto rounded" style={{ width: '50%' }}></div>
        </div>

        {/* Dashboard Loading */}
        <div className="card card-p-6">
          <div className="skeleton h-8 mb-6 rounded" style={{ width: '16rem' }}></div>
          <div className="grid grid-cols-1 gap-6" style={{ 
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))'
          }}>
            {[...Array(4)].map((_, i) => (
              <div key={i} className="skeleton h-24 rounded"></div>
            ))}
          </div>
        </div>
        
        {/* Narratives Loading */}
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="card card-p-6">
              <div className="skeleton h-6 mb-4 rounded" style={{ width: '75%' }}></div>
              <div className="skeleton h-4 mb-2 rounded" style={{ width: '50%' }}></div>
              <div className="skeleton h-4 rounded" style={{ width: '25%' }}></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center" style={{ minHeight: '60vh' }}>
        <div className="card card-p-6 text-center max-w-md">
          <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Connection Failed</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button 
            onClick={() => window.location.reload()}
            className="btn-primary"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center py-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Iran-Israel Narrative Intelligence
        </h1>
        <p className="text-lg text-gray-600 max-w-3xl mx-auto">
          Real-time analysis of conflicting narratives across news, social media, and video platforms. 
          Track how stories evolve and discover source relationships.
        </p>
      </div>

      {/* Dashboard Section */}
      <div className="card card-p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900">System Overview</h2>
          <div className="flex items-center space-x-2 text-green-600">
            <div className="w-2 h-2 rounded-full status-active"></div>
            <span className="text-sm font-medium">Live Data</span>
          </div>
        </div>
        <Dashboard />
      </div>

      {/* Narratives Section */}
      <div className="space-y-6">
        <div className="card card-p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Active Narratives</h2>
              <p className="text-gray-600">
                Tracking {narratives.length} narrative clusters from Iran-Israel conflict coverage
              </p>
            </div>
            
            {/* Controls */}
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <label className="text-sm font-medium text-gray-700">Sort by:</label>
                <select 
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as 'recent' | 'sources')}
                  className="input text-sm"
                >
                  <option value="recent">Most Recent</option>
                  <option value="sources">Most Sources</option>
                </select>
              </div>
              
              <div className="flex items-center space-x-2 text-gray-500 text-sm">
                <div className="w-2 h-2 rounded-full status-active"></div>
                <span>Updated {new Date().toLocaleTimeString()}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Narratives Grid */}
        {narratives.length === 0 ? (
          <div className="card text-center" style={{ padding: '3rem' }}>
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-700 mb-2">No Narratives Found</h3>
            <p className="text-gray-500 mb-4">Try refreshing the data or check back in a few minutes.</p>
            <button className="btn-primary" onClick={() => window.location.reload()}>
              Refresh Data
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {sortedNarratives.map((narrative) => (
              <Card key={narrative.id} narrative={narrative} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
} 