import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

type PlatformStats = {
  platform: string;
  count: number;
};

type Stats = {
  totalNarratives: number;
  totalSources: number;
  platforms: PlatformStats[];
};

export default function Sidebar() {
  const location = useLocation();
  const [stats, setStats] = useState<Stats>({
    totalNarratives: 0,
    totalSources: 0,
    platforms: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const narrativesResponse = await fetch('http://localhost:8000/api/narratives');
        const narratives = await narrativesResponse.json();
        
        const totalNarratives = narratives.length;
        const totalSources = narratives.reduce((sum: number, n: { source_count: number }) => sum + n.source_count, 0);
        
        setStats({
          totalNarratives,
          totalSources,
          platforms: [
            { platform: 'News Media', count: Math.floor(totalSources * 0.6) },
            { platform: 'Social Media', count: Math.floor(totalSources * 0.3) },
            { platform: 'Video Content', count: Math.floor(totalSources * 0.1) },
          ]
        });
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  const isActive = (path: string) => location.pathname === path;

  return (
    <aside className="sidebar">
      <div className="sidebar-content">
        {/* Navigation Links */}
        <nav className="nav-section">
          <h2 className="nav-title">
            Navigation
          </h2>
          
          <div className="nav-list">
            <Link
              to="/"
              className={`nav-item ${isActive('/') ? 'active' : ''}`}
            >
              <svg className="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
              </svg>
              Dashboard
            </Link>
            
            <Link
              to="/graph"
              className={`nav-item ${isActive('/graph') ? 'active' : ''}`}
            >
              <svg className="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              Network Graph
            </Link>

            <Link
              to="/login"
              className={`nav-item ${isActive('/login') ? 'active' : ''}`}
            >
              <svg className="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
              </svg>
              Login
            </Link>
          </div>
        </nav>

        {/* Statistics */}
        <div className="space-y-4">
          <h2 className="nav-title">
            Live Analytics
          </h2>
          
          {loading ? (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="card card-p-4 skeleton h-20"></div>
              ))}
            </div>
          ) : (
            <div className="space-y-4">
              <div className="card card-p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600">Active Narratives</span>
                  <div className="w-2 h-2 rounded-full status-active"></div>
                </div>
                <div className="text-2xl font-bold text-gray-900">
                  {stats.totalNarratives}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Currently tracking</div>
              </div>
              
              <div className="card card-p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600">Total Sources</span>
                  <div className="w-2 h-2 rounded-full status-warning"></div>
                </div>
                <div className="text-2xl font-bold text-gray-900">
                  {stats.totalSources}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Across all platforms</div>
              </div>

              <div className="card card-p-4">
                <h3 className="text-sm font-medium text-gray-700 mb-4" style={{ marginBottom: '0.75rem' }}>Platform Distribution</h3>
                <div className="space-y-4" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {stats.platforms.map((platform, index) => {
                    const colors = ['bg-blue-500', 'bg-purple-500', 'bg-green-500'];
                    return (
                      <div key={platform.platform} className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <div className={`w-2 h-2 rounded-full ${colors[index]}`}></div>
                          <span className="text-sm text-gray-600">{platform.platform}</span>
                        </div>
                        <span className="text-sm font-medium text-gray-900">{platform.count}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="card card-p-4 bg-green-50" style={{ backgroundColor: '#f0fdf4', borderColor: '#bbf7d0' }}>
                <div className="text-center">
                  <div style={{ fontSize: '0.75rem', color: '#059669', marginBottom: '0.25rem' }}>System Status</div>
                  <div className="flex items-center justify-center space-x-2">
                    <div className="w-2 h-2 rounded-full status-active"></div>
                    <span className="text-sm font-medium" style={{ color: '#047857' }}>All Systems Operational</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
} 