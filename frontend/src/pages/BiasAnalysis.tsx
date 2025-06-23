import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';

interface BiasIndicators {
  loaded_language?: string[];
  missing_context?: string[];
  selective_facts?: string[];
  emotional_manipulation?: string[];
}

interface BiasAnalysis {
  id: string;
  analysis_type: string;
  bias_indicators: BiasIndicators;
  blind_spots?: string[];
  missing_context?: string[];
  confidence_score: number;
  created_at: string;
}

interface AlternativePerspective {
  id: string;
  perspective_type: string;
  perspective_text: string;
  supporting_sources?: string[];
  confidence_score: number;
  created_at: string;
}

interface FactCheck {
  id: string;
  verification_status: string;
  evidence_text?: string;
  accuracy_score: number;
  context_provided: boolean;
  academic_source_title: string;
  created_at: string;
}

interface SourceBiasDetail {
  id: string;
  name: string;
  political_bias?: number;
  factual_accuracy?: number;
  emotional_tone?: number;
  sensationalism_score?: number;
  confidence_score?: number;
  analysis_method?: string;
  last_analysis_date?: string;
}

interface SourceDetail {
  id: number;
  platform: string;
  url: string;
  created_at: string;
  bias?: SourceBiasDetail;
  bias_analyses: BiasAnalysis[];
  alternative_perspectives: AlternativePerspective[];
  fact_checks: FactCheck[];
}

export default function BiasAnalysis() {
  const { sourceId } = useParams<{ sourceId: string }>();
  const [sourceDetail, setSourceDetail] = useState<SourceDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  useEffect(() => {
    if (sourceId) {
      fetchSourceDetail(parseInt(sourceId));
    }
  }, [sourceId]);

  const fetchSourceDetail = async (id: number) => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8000/api/bias/sources/${id}/bias-analysis`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setSourceDetail(data);
    } catch (error) {
      console.error('Failed to fetch source detail:', error);
      setError(error instanceof Error ? error.message : 'Failed to load bias analysis');
    } finally {
      setLoading(false);
    }
  };

  const triggerAnalysis = async () => {
    if (!sourceId) return;
    
    try {
      setIsAnalyzing(true);
      const response = await fetch(`http://localhost:8000/api/bias/sources/${sourceId}/analyze`, {
        method: 'POST',
      });
      
      if (response.ok) {
        // Refresh data after a short delay
        setTimeout(() => {
          fetchSourceDetail(parseInt(sourceId));
        }, 3000);
      }
    } catch (error) {
      console.error('Failed to trigger analysis:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getBiasColor = (score?: number) => {
    if (score === undefined || score === null) return 'text-gray-500';
    if (score < -0.3) return 'text-red-600'; // Left
    if (score > 0.3) return 'text-blue-600'; // Right
    return 'text-green-600'; // Center
  };

  const getAccuracyColor = (score?: number) => {
    if (score === undefined || score === null) return 'text-gray-500';
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getVerificationColor = (status: string) => {
    switch (status) {
      case 'verified': return 'text-green-600 bg-green-50';
      case 'partially_verified': return 'text-yellow-600 bg-yellow-50';
      case 'disputed': return 'text-orange-600 bg-orange-50';
      case 'false': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading bias analysis...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center text-red-600">
          <p className="text-xl mb-4">Failed to load bias analysis</p>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!sourceDetail) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-xl text-gray-600">Source not found</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Bias Analysis</h1>
            <p className="text-gray-600">{sourceDetail.platform} • Source ID: {sourceDetail.id}</p>
          </div>
          <button
            onClick={triggerAnalysis}
            disabled={isAnalyzing}
            className={`px-4 py-2 rounded-lg font-medium ${
              isAnalyzing 
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                : 'bg-blue-500 text-white hover:bg-blue-600'
            }`}
          >
            {isAnalyzing ? 'Analyzing...' : 'Re-analyze'}
          </button>
        </div>
        
        <a 
          href={sourceDetail.url} 
          target="_blank" 
          rel="noopener noreferrer"
          className="text-blue-500 hover:underline"
        >
          View Original Source
        </a>
      </div>

      {/* Bias Metrics */}
      {sourceDetail.bias && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Bias Metrics</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className={`text-2xl font-bold ${getBiasColor(sourceDetail.bias.political_bias)}`}>
                {sourceDetail.bias.political_bias?.toFixed(2) ?? 'N/A'}
              </div>
              <div className="text-sm text-gray-600">Political Bias</div>
              <div className="text-xs text-gray-500">-1.0 (Left) to 1.0 (Right)</div>
            </div>
            
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className={`text-2xl font-bold ${getAccuracyColor(sourceDetail.bias.factual_accuracy)}`}>
                {sourceDetail.bias.factual_accuracy?.toFixed(2) ?? 'N/A'}
              </div>
              <div className="text-sm text-gray-600">Factual Accuracy</div>
              <div className="text-xs text-gray-500">0.0 (Low) to 1.0 (High)</div>
            </div>
            
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className={`text-2xl font-bold ${getBiasColor(sourceDetail.bias.emotional_tone)}`}>
                {sourceDetail.bias.emotional_tone?.toFixed(2) ?? 'N/A'}
              </div>
              <div className="text-sm text-gray-600">Emotional Tone</div>
              <div className="text-xs text-gray-500">-1.0 (Negative) to 1.0 (Positive)</div>
            </div>
            
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className={`text-2xl font-bold ${getAccuracyColor(1 - (sourceDetail.bias.sensationalism_score ?? 0))}`}>
                {sourceDetail.bias.sensationalism_score?.toFixed(2) ?? 'N/A'}
              </div>
              <div className="text-sm text-gray-600">Sensationalism</div>
              <div className="text-xs text-gray-500">0.0 (Neutral) to 1.0 (High)</div>
            </div>
          </div>
        </div>
      )}

      {/* Bias Analysis Details */}
      {sourceDetail.bias_analyses.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Bias Indicators</h2>
          {sourceDetail.bias_analyses.map((analysis) => (
            <div key={analysis.id} className="mb-6 p-4 border rounded-lg">
              <div className="flex items-center justify-between mb-3">
                <span className="font-medium capitalize">{analysis.analysis_type.replace('_', ' ')}</span>
                <span className="text-sm text-gray-500">
                  Confidence: {(analysis.confidence_score * 100).toFixed(0)}%
                </span>
              </div>
              
              {analysis.bias_indicators && Object.keys(analysis.bias_indicators).length > 0 && (
                <div className="space-y-3">
                  {Object.entries(analysis.bias_indicators).map(([key, values]) => (
                    values && Array.isArray(values) && values.length > 0 && (
                      <div key={key}>
                        <div className="font-medium text-sm text-gray-700 capitalize mb-1">
                          {key.replace('_', ' ')}:
                        </div>
                        <ul className="list-disc list-inside text-sm text-gray-600 ml-2">
                          {values.map((item, idx) => (
                            <li key={idx}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    )
                  ))}
                </div>
              )}
              
              {analysis.blind_spots && analysis.blind_spots.length > 0 && (
                <div className="mt-3">
                  <div className="font-medium text-sm text-gray-700 mb-1">Blind Spots:</div>
                  <ul className="list-disc list-inside text-sm text-gray-600 ml-2">
                    {analysis.blind_spots.map((spot, idx) => (
                      <li key={idx}>{spot}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Alternative Perspectives */}
      {sourceDetail.alternative_perspectives.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Alternative Perspectives</h2>
          {sourceDetail.alternative_perspectives.map((perspective) => (
            <div key={perspective.id} className="mb-6 p-4 border-l-4 border-blue-500 bg-blue-50">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium capitalize text-blue-800">
                  {perspective.perspective_type.replace('_', ' ')}
                </span>
                <span className="text-sm text-blue-600">
                  Confidence: {(perspective.confidence_score * 100).toFixed(0)}%
                </span>
              </div>
              <p className="text-gray-700 mb-3">{perspective.perspective_text}</p>
              {perspective.supporting_sources && perspective.supporting_sources.length > 0 && (
                <div>
                  <div className="font-medium text-sm text-blue-700 mb-1">Supporting Sources:</div>
                  <ul className="list-disc list-inside text-sm text-blue-600 ml-2">
                    {perspective.supporting_sources.map((source, idx) => (
                      <li key={idx}>{source}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Fact Checks */}
      {sourceDetail.fact_checks.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Fact Checks</h2>
          {sourceDetail.fact_checks.map((factCheck) => (
            <div key={factCheck.id} className="mb-4 p-4 border rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getVerificationColor(factCheck.verification_status)}`}>
                  {factCheck.verification_status.replace('_', ' ').toUpperCase()}
                </span>
                <span className="text-sm text-gray-500">
                  Accuracy: {(factCheck.accuracy_score * 100).toFixed(0)}%
                </span>
              </div>
              <div className="text-sm text-gray-600 mb-2">
                Verified against: <span className="font-medium">{factCheck.academic_source_title}</span>
              </div>
              {factCheck.evidence_text && (
                <p className="text-gray-700">{factCheck.evidence_text}</p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* No Analysis Available */}
      {sourceDetail.bias_analyses.length === 0 && 
       sourceDetail.alternative_perspectives.length === 0 && 
       sourceDetail.fact_checks.length === 0 && (
        <div className="bg-white rounded-lg shadow-md p-8 text-center">
          <div className="text-gray-500 mb-4">
            <svg className="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Analysis Available</h3>
            <p className="text-gray-600">
              This source hasn't been analyzed yet. Click "Re-analyze" to start the bias analysis process.
            </p>
          </div>
        </div>
      )}
    </div>
  );
} 