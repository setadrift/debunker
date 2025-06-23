import { useState } from 'react';
import { Link } from 'react-router-dom';
import AuthGuard from './AuthGuard';

export default function Header() {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      const response = await fetch('http://localhost:8000/api/refresh', {
        method: 'POST',
      });
      if (response.ok) {
        setLastUpdated(new Date());
      }
    } catch (error) {
      console.error('Failed to refresh data:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  return (
    <header className="header">
      <div className="header-content">
        {/* Logo and Title */}
        <div className="logo-section">
          <Link to="/" className="logo-link">
            <div className="logo-icon">
              <span className="logo-text">II</span>
            </div>
            <div>
              <h1 className="site-title">
                Narrative Tracker
              </h1>
              <p className="site-subtitle">
                Iran-Israel Conflict Analysis
              </p>
            </div>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="main-nav">
          <Link to="/" className="nav-link">
            Dashboard
          </Link>
          <Link to="/graph" className="nav-link">
            Network Graph
          </Link>
        </nav>

        {/* Status and Controls */}
        <div className="header-controls">
          {lastUpdated && (
            <div className="status-indicator">
              <div className="w-2 h-2 rounded-full status-active"></div>
              <span>
                {lastUpdated.toLocaleTimeString()}
              </span>
            </div>
          )}
          
          <AuthGuard>
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className={`btn-primary ${isRefreshing ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              {isRefreshing ? (
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4" style={{ 
                    border: '2px solid white', 
                    borderTop: '2px solid transparent', 
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite'
                  }}></div>
                  <span>Updating...</span>
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  <span>Refresh</span>
                </div>
              )}
            </button>
          </AuthGuard>
        </div>
      </div>
    </header>
  );
} 