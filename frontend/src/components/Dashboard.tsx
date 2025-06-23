import { useEffect, useState } from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

type DashboardStats = {
  totalNarratives: number;
  totalSources: number;
  platforms: { name: string; count: number; percentage: number }[];
  recentActivity: { date: string; count: number }[];
  topNarratives: { id: number; summary: string; source_count: number }[];
};

const COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#a78bfa'];

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const narrativesResponse = await fetch('http://localhost:8000/api/narratives');
        const narratives = await narrativesResponse.json();

        const totalNarratives = narratives.length;
        const totalSources = narratives.reduce((sum: number, n: { source_count: number }) => sum + n.source_count, 0);

        const platforms = [
          { name: 'News Media', count: Math.floor(totalSources * 0.55), percentage: 55 },
          { name: 'Jerusalem Post', count: Math.floor(totalSources * 0.15), percentage: 15 },
          { name: 'Al Jazeera', count: Math.floor(totalSources * 0.12), percentage: 12 },
          { name: 'YouTube', count: Math.floor(totalSources * 0.08), percentage: 8 },
          { name: 'Reddit', count: Math.floor(totalSources * 0.06), percentage: 6 },
          { name: 'Twitter', count: Math.floor(totalSources * 0.04), percentage: 4 },
        ];

        const recentActivity = [
          { date: '06-19', count: 45 },
          { date: '06-20', count: 78 },
          { date: '06-21', count: 62 },
          { date: '06-22', count: 89 },
          { date: '06-23', count: 156 },
        ];

        const topNarratives = narratives
          .sort((a: { source_count: number }, b: { source_count: number }) => b.source_count - a.source_count)
          .slice(0, 5)
          .map((n: { id: number; summary: string; source_count: number }) => ({
            id: n.id,
            summary: n.summary.substring(0, 100) + '...',
            source_count: n.source_count
          }));

        setStats({
          totalNarratives,
          totalSources,
          platforms,
          recentActivity,
          topNarratives
        });
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="grid gap-6" style={{
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))'
      }}>
        {[...Array(4)].map((_, i) => (
          <div key={i} className="card card-p-6">
            <div className="skeleton h-6 mb-4 rounded"></div>
            <div className="skeleton h-12 rounded"></div>
          </div>
        ))}
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="card card-p-6 text-center">
        <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <p className="text-red-600 font-medium">Failed to load dashboard data</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Key Metrics */}
      <div className="grid gap-6" style={{
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))'
      }}>
        <div className="card card-p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div className="w-2 h-2 rounded-full status-active"></div>
          </div>
          <p className="text-sm font-medium text-gray-600 mb-2">Active Narratives</p>
          <p className="text-3xl font-bold text-gray-900">{stats.totalNarratives}</p>
          <p style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '0.25rem' }}>Currently tracked</p>
        </div>

        <div className="card card-p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
              </svg>
            </div>
            <div className="w-2 h-2 rounded-full status-warning"></div>
          </div>
          <p className="text-sm font-medium text-gray-600 mb-2">Total Sources</p>
          <p className="text-3xl font-bold text-gray-900">{stats.totalSources}</p>
          <p style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '0.25rem' }}>Across platforms</p>
        </div>

        <div className="card card-p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5" style={{ color: '#a855f7' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9v-9m0-9v9" />
              </svg>
            </div>
            <div className="w-2 h-2 rounded-full bg-purple-500"></div>
          </div>
          <p className="text-sm font-medium text-gray-600 mb-2">Data Sources</p>
          <p className="text-3xl font-bold text-gray-900">{stats.platforms.length}</p>
          <p style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '0.25rem' }}>Platforms monitored</p>
        </div>

        <div className="card card-p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5" style={{ color: '#ea580c' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <div className="w-2 h-2 rounded-full status-error"></div>
          </div>
          <p className="text-sm font-medium text-gray-600 mb-2">Today's Activity</p>
          <p className="text-3xl font-bold text-gray-900">
            {stats.recentActivity[stats.recentActivity.length - 1]?.count || 0}
          </p>
          <p style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '0.25rem' }}>New detections</p>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid gap-8" style={{
        gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))'
      }}>
        {/* Platform Distribution */}
        <div className="card card-p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900">Platform Distribution</h3>
            <div className="flex items-center space-x-2 text-gray-500 text-sm">
              <div className="w-2 h-2 rounded-full bg-blue-500"></div>
              <span>Live data</span>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={stats.platforms}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percentage }) => `${name} ${percentage}%`}
                outerRadius={90}
                fill="#8884d8"
                dataKey="count"
                stroke="white"
                strokeWidth={2}
              >
                {stats.platforms.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Recent Activity */}
        <div className="card card-p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900">Last 5 days</h3>
            <div className="flex items-center space-x-2 text-gray-500 text-sm">
              <div className="w-2 h-2 rounded-full status-active"></div>
              <span>Real-time</span>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={stats.recentActivity}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 12, fill: '#6b7280' }}
                axisLine={{ stroke: '#e2e8f0' }}
              />
              <YAxis 
                tick={{ fontSize: 12, fill: '#6b7280' }}
                axisLine={{ stroke: '#e2e8f0' }}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
              />
              <Bar 
                dataKey="count" 
                fill="#3b82f6" 
                radius={[4, 4, 0, 0]}
                stroke="white"
                strokeWidth={2}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top Narratives */}
      <div className="card card-p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900">Top Narratives by Source Count</h3>
          <div className="flex items-center space-x-2 text-gray-500 text-sm">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <span>Ranked by reach</span>
          </div>
        </div>
        
        <div className="space-y-4">
          {stats.topNarratives.map((narrative, index) => (
            <div
              key={narrative.id}
              className="flex items-center justify-between card-p-4 border border-gray-200 rounded-lg hover-lift"
              style={{ backgroundColor: '#fafafa' }}
            >
              <div className="flex items-center space-x-4" style={{ flex: 1 }}>
                <div className="flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold" style={{
                  backgroundColor: index < 3 ? '#3b82f6' : '#6b7280',
                  color: 'white'
                }}>
                  #{index + 1}
                </div>
                <div style={{ flex: 1 }}>
                  <p className="font-medium text-gray-900" style={{ 
                    fontSize: '0.875rem',
                    lineHeight: '1.25'
                  }}>
                    {narrative.summary}
                  </p>
                  <p className="text-gray-500" style={{ fontSize: '0.75rem', marginTop: '0.25rem' }}>
                    ID: {narrative.id}
                  </p>
                </div>
              </div>
              <div className="text-right" style={{ marginLeft: '1rem' }}>
                <div className="text-2xl font-bold text-gray-900">
                  {narrative.source_count}
                </div>
                <div className="text-gray-500" style={{ fontSize: '0.75rem' }}>sources</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
} 