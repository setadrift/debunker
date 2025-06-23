import { Link } from "react-router-dom";

type Narrative = {
  id: number;
  summary: string;
  source_count: number;
  last_seen: string;
  first_seen: string;
};

export default function Card({ narrative }: { narrative: Narrative }) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const calculateDaysActive = () => {
    const first = new Date(narrative.first_seen);
    const last = new Date(narrative.last_seen);
    const diffTime = Math.abs(last.getTime() - first.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const getTrendIndicator = () => {
    const hoursAgo = (Date.now() - new Date(narrative.last_seen).getTime()) / (1000 * 60 * 60);
    
    if (hoursAgo < 2) {
      return { 
        label: 'Breaking', 
        style: 'badge-error',
        icon: '🔥'
      };
    } else if (hoursAgo < 12) {
      return { 
        label: 'Trending', 
        style: 'badge-warning',
        icon: '📈'
      };
    } else if (hoursAgo < 24) {
      return { 
        label: 'Active', 
        style: 'badge-success',
        icon: '📊'
      };
    } else {
      return { 
        label: 'Cooling', 
        style: 'badge-gray',
        icon: '📉'
      };
    }
  };

  const trend = getTrendIndicator();
  const daysActive = calculateDaysActive();

  return (
    <div className="card hover-lift card-p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4" style={{ alignItems: 'flex-start' }}>
        <div className="flex items-center space-x-4" style={{ gap: '0.75rem' }}>
          <div className={`badge ${trend.style}`}>
            <span style={{ marginRight: '0.25rem' }}>{trend.icon}</span>
            {trend.label}
          </div>
          <div className="flex items-center text-gray-500 text-sm" style={{ gap: '0.25rem' }}>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Active for {daysActive} day{daysActive !== 1 ? 's' : ''}</span>
          </div>
        </div>
        
        <div style={{ 
          fontSize: '0.75rem', 
          color: '#9ca3af', 
          backgroundColor: '#f3f4f6', 
          padding: '0.25rem 0.5rem', 
          borderRadius: '0.25rem' 
        }}>
          ID: {narrative.id}
        </div>
      </div>

      {/* Summary */}
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-gray-900" style={{ lineHeight: '1.5' }}>
          {narrative.summary}
        </h2>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-blue-50 rounded-lg" style={{ 
          padding: '0.75rem',
          border: '1px solid #bfdbfe'
        }}>
          <div className="flex items-center justify-between mb-2" style={{ marginBottom: '0.25rem' }}>
            <span className="text-sm font-medium text-blue-700">Sources</span>
            <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9.5a2.5 2.5 0 00-2.5-2.5H15" />
            </svg>
          </div>
          <div className="text-2xl font-bold" style={{ color: '#1e3a8a' }}>
            {narrative.source_count}
          </div>
        </div>
        
        <div className="bg-green-50 rounded-lg" style={{ 
          padding: '0.75rem',
          border: '1px solid #bbf7d0'
        }}>
          <div className="flex items-center justify-between mb-2" style={{ marginBottom: '0.25rem' }}>
            <span className="text-sm font-medium text-green-700">Latest</span>
            <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div className="text-sm font-semibold" style={{ color: '#14532d' }}>
            {formatDate(narrative.last_seen)}
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className="bg-gray-50 rounded-lg mb-4" style={{ 
        padding: '0.75rem',
        border: '1px solid #d1d5db'
      }}>
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: '#4ade80' }}></div>
            <span className="text-gray-600">Started: {formatDate(narrative.first_seen)}</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: '#60a5fa' }}></div>
            <span className="text-gray-600">Updated: {formatDate(narrative.last_seen)}</span>
          </div>
        </div>
      </div>

      {/* Action Button */}
      <div className="flex items-center justify-between">
        <Link
          to={`/narratives/${narrative.id}`}
          className="btn-primary"
        >
          <span>Explore Details</span>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </Link>
        
        <div className="flex items-center text-gray-400" style={{ gap: '0.25rem', fontSize: '0.75rem' }}>
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
          <span>Live tracking</span>
        </div>
      </div>
    </div>
  );
} 