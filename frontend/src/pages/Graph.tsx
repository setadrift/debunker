import { useState } from 'react';
import NetworkGraph from '../components/NetworkGraph';

export default function GraphPage() {
  const [isInfoOpen, setIsInfoOpen] = useState(false);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Source Network Graph</h1>
          <p className="text-gray-600" style={{ marginTop: '0.25rem' }}>
            Interactive visualization showing relationships between news sources and platforms
          </p>
        </div>
        
        <button
          onClick={() => setIsInfoOpen(!isInfoOpen)}
          className="btn-secondary"
        >
          <svg className="w-4 h-4" style={{ marginRight: '0.5rem' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          How to Read This Graph
        </button>
      </div>

      {/* Info Panel */}
      {isInfoOpen && (
        <div className="card card-p-6 bg-blue-50 border-blue-200">
          <h3 className="text-lg font-semibold mb-4" style={{ color: '#1e3a8a', marginBottom: '0.75rem' }}>Understanding the Network Graph</h3>
          <div className="grid gap-6 text-sm" style={{ 
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            color: '#1e40af'
          }}>
            <div>
              <h4 className="font-medium mb-2">Nodes (Circles)</h4>
              <ul className="space-y-2" style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                <li>• Each node represents a news platform or source</li>
                <li>• Node size indicates the number of articles from that source</li>
                <li>• Different colors represent different platform types</li>
                <li>• Hover over nodes to see engagement metrics</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-2">Links (Lines)</h4>
              <ul className="space-y-2" style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                <li>• Lines connect sources that appear in the same narrative cluster</li>
                <li>• Thicker lines indicate stronger relationships</li>
                <li>• Clustered sources often have similar perspectives</li>
              </ul>
            </div>
          </div>
          <div style={{ 
            marginTop: '1rem', 
            padding: '0.75rem',
            backgroundColor: '#dbeafe',
            borderRadius: '0.5rem'
          }}>
            <p className="text-sm" style={{ color: '#1d4ed8' }}>
              <strong>Tip:</strong> Drag nodes to rearrange the graph, zoom with your mouse wheel, and click on nodes for detailed information.
            </p>
          </div>
        </div>
      )}

      {/* Controls */}
      <div className="card card-p-4">
        <div className="flex items-center gap-4" style={{ flexWrap: 'wrap' }}>
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700">Legend:</span>
            <div className="flex items-center space-x-4">
              <div className="flex items-center" style={{ gap: '0.25rem' }}>
                <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                <span style={{ fontSize: '0.75rem', color: '#4b5563' }}>News Media</span>
              </div>
              <div className="flex items-center" style={{ gap: '0.25rem' }}>
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span style={{ fontSize: '0.75rem', color: '#4b5563' }}>Social Media</span>
              </div>
              <div className="flex items-center" style={{ gap: '0.25rem' }}>
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#f97316' }}></div>
                <span style={{ fontSize: '0.75rem', color: '#4b5563' }}>Video Content</span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700">Graph Settings:</span>
            <button className="btn-secondary text-sm" style={{ fontSize: '0.75rem' }}>
              Reset Zoom
            </button>
            <button className="btn-secondary text-sm" style={{ fontSize: '0.75rem' }}>
              Center Graph
            </button>
          </div>
        </div>
      </div>

      {/* Graph Container */}
      <div className="card" style={{ overflow: 'hidden' }}>
        <div className="border-b bg-gray-50" style={{ padding: '1rem', borderBottom: '1px solid #e5e7eb' }}>
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">Network Visualization</h3>
            <div className="text-sm text-gray-500">
              Interactive • Real-time data • Drag to explore
            </div>
          </div>
        </div>
        
        {/* Graph Component */}
        <div style={{ 
          position: 'relative',
          height: 'calc(100vh - 400px)', 
          minHeight: '600px' 
        }}>
          <NetworkGraph />
          
          {/* Overlay Instructions */}
          <div style={{
            position: 'absolute',
            top: '1rem',
            right: '1rem',
            backgroundColor: 'rgba(255, 255, 255, 0.9)',
            padding: '0.75rem',
            borderRadius: '0.5rem',
            boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
            fontSize: '0.75rem',
            color: '#4b5563',
            maxWidth: '20rem'
          }}>
            <p className="font-medium" style={{ marginBottom: '0.25rem' }}>Quick Controls:</p>
            <p>• Drag: Move nodes</p>
            <p>• Scroll: Zoom in/out</p>
            <p>• Hover: View details</p>
          </div>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid gap-6" style={{
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))'
      }}>
        <div className="card card-p-6">
          <div className="flex items-center">
            <div style={{ 
              padding: '0.5rem',
              backgroundColor: '#dbeafe',
              borderRadius: '0.5rem'
            }}>
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9v-9m0-9v9" />
              </svg>
            </div>
            <div style={{ marginLeft: '1rem' }}>
              <p className="text-sm font-medium text-gray-600">Connected Sources</p>
              <p className="text-2xl font-bold text-gray-900">12+</p>
            </div>
          </div>
        </div>

        <div className="card card-p-6">
          <div className="flex items-center">
            <div style={{ 
              padding: '0.5rem',
              backgroundColor: '#dcfce7',
              borderRadius: '0.5rem'
            }}>
              <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
            </div>
            <div style={{ marginLeft: '1rem' }}>
              <p className="text-sm font-medium text-gray-600">Network Links</p>
              <p className="text-2xl font-bold text-gray-900">25+</p>
            </div>
          </div>
        </div>

        <div className="card card-p-6">
          <div className="flex items-center">
            <div style={{ 
              padding: '0.5rem',
              backgroundColor: '#f3e8ff',
              borderRadius: '0.5rem'
            }}>
              <svg className="w-5 h-5" style={{ color: '#a855f7' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </div>
            <div style={{ marginLeft: '1rem' }}>
              <p className="text-sm font-medium text-gray-600">Narrative Clusters</p>
              <p className="text-2xl font-bold text-gray-900">2</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 