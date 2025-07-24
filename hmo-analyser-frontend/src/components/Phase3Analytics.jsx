import React, { useState } from 'react';
import AvailabilityHeatmap from './AvailabilityHeatmap';

const Phase3Analytics = ({ propertyId }) => {
  const [activeTab, setActiveTab] = useState('heatmap');

  const tabs = [
    { 
      id: 'heatmap', 
      label: '📅 Availability Heatmap', 
      description: 'Visual calendar showing occupancy patterns over time'
    },
    { 
      id: 'portfolio', 
      label: '📊 Portfolio Comparison', 
      description: 'Compare this property against your portfolio',
      comingSoon: true 
    },
    { 
      id: 'predictions', 
      label: '🔮 Predictive Insights', 
      description: 'AI-powered predictions and recommendations',
      comingSoon: true 
    }
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'heatmap':
        return <AvailabilityHeatmap propertyId={propertyId} />;
      
      case 'portfolio':
        return (
          <div className="card">
            <h3 className="card-title">📊 Portfolio Comparison</h3>
            <div style={{ 
              textAlign: 'center', 
              padding: '3rem',
              backgroundColor: '#f8fafc',
              borderRadius: '8px',
              border: '1px dashed #cbd5e1'
            }}>
              <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🚧</div>
              <h4 style={{ color: '#64748b', marginBottom: '1rem' }}>Coming Soon</h4>
              <p style={{ color: '#64748b', fontSize: '0.875rem', maxWidth: '400px', margin: '0 auto' }}>
                Portfolio comparison tools will allow you to benchmark this property against 
                your entire portfolio and market averages.
              </p>
              <div style={{ 
                marginTop: '2rem',
                padding: '1rem',
                backgroundColor: '#fef3c7',
                borderRadius: '6px',
                fontSize: '0.875rem'
              }}>
                <strong>Planned Features:</strong>
                <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem', textAlign: 'left' }}>
                  <li>Side-by-side property performance comparison</li>
                  <li>Market benchmarking vs local averages</li>
                  <li>ROI analysis and ranking</li>
                  <li>Geographic clustering insights</li>
                </ul>
              </div>
            </div>
          </div>
        );
      
      case 'predictions':
        return (
          <div className="card">
            <h3 className="card-title">🔮 Predictive Insights</h3>
            <div style={{ 
              textAlign: 'center', 
              padding: '3rem',
              backgroundColor: '#f8fafc',
              borderRadius: '8px',
              border: '1px dashed #cbd5e1'
            }}>
              <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🤖</div>
              <h4 style={{ color: '#64748b', marginBottom: '1rem' }}>AI-Powered Analytics Coming Soon</h4>
              <p style={{ color: '#64748b', fontSize: '0.875rem', maxWidth: '500px', margin: '0 auto' }}>
                Machine learning models will analyze your property data to provide 
                intelligent predictions and optimization recommendations.
              </p>
              <div style={{ 
                marginTop: '2rem',
                padding: '1rem',
                backgroundColor: '#e0e7ff',
                borderRadius: '6px',
                fontSize: '0.875rem'
              }}>
                <strong>🧠 Planned AI Features:</strong>
                <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem', textAlign: 'left' }}>
                  <li><strong>Vacancy Duration Prediction:</strong> How long will rooms stay available?</li>
                  <li><strong>Price Optimization:</strong> Optimal rent to minimize vacancy time</li>
                  <li><strong>Seasonal Forecasting:</strong> Best times to adjust prices or list rooms</li>
                  <li><strong>Market Trend Analysis:</strong> Property value trajectory predictions</li>
                  <li><strong>Investment Scoring:</strong> Automated property ranking and recommendations</li>
                </ul>
              </div>
            </div>
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <div style={{ marginTop: '2rem' }}>
      {/* Phase 3 Header */}
      <div style={{ 
        marginBottom: '2rem',
        padding: '1rem',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        borderRadius: '12px',
        color: 'white'
      }}>
        <h2 style={{ 
          fontSize: '1.5rem', 
          fontWeight: 'bold', 
          marginBottom: '0.5rem',
          color: 'white'
        }}>
          🚀 Phase 3: Advanced Analytics
        </h2>
        <p style={{ 
          fontSize: '0.875rem',
          opacity: 0.9,
          margin: 0
        }}>
          Sophisticated analytics and predictive insights for data-driven investment decisions
        </p>
      </div>

      {/* Tab Navigation */}
      <div style={{ 
        display: 'flex', 
        gap: '0.5rem', 
        marginBottom: '2rem',
        borderBottom: '1px solid #e5e7eb',
        paddingBottom: '1rem',
        overflowX: 'auto',
        flexWrap: 'wrap'
      }}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '1rem 1.5rem',
              border: 'none',
              borderRadius: '8px',
              backgroundColor: activeTab === tab.id ? '#667eea' : '#f1f5f9',
              color: activeTab === tab.id ? 'white' : '#64748b',
              fontWeight: activeTab === tab.id ? '600' : '500',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              fontSize: '0.875rem',
              position: 'relative',
              minWidth: '200px',
              textAlign: 'left'
            }}
            disabled={tab.comingSoon}
          >
            <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>
              {tab.label}
              {tab.comingSoon && (
                <span style={{ 
                  fontSize: '0.75rem',
                  backgroundColor: activeTab === tab.id ? 'rgba(255,255,255,0.2)' : '#fbbf24',
                  color: activeTab === tab.id ? 'white' : '#92400e',
                  padding: '2px 6px',
                  borderRadius: '4px',
                  marginLeft: '0.5rem'
                }}>
                  Soon
                </span>
              )}
            </div>
            <div style={{ 
              fontSize: '0.75rem',
              opacity: 0.8,
              lineHeight: '1.3'
            }}>
              {tab.description}
            </div>
          </button>
        ))}
      </div>

      {/* Active Tab Content */}
      {renderTabContent()}

      {/* Development Status Info */}
      <div style={{ 
        marginTop: '2rem',
        padding: '1rem',
        backgroundColor: '#f0f9ff',
        borderRadius: '8px',
        border: '1px solid #bae6fd',
        fontSize: '0.875rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
          <span style={{ fontSize: '1.2rem' }}>ℹ️</span>
          <strong style={{ color: '#0369a1' }}>Phase 3 Development Status</strong>
        </div>
        <div style={{ color: '#0c4a6e' }}>
          <div style={{ marginBottom: '0.5rem' }}>
            ✅ <strong>Availability Heatmap:</strong> Fully functional with interactive calendar view
          </div>
          <div style={{ marginBottom: '0.5rem' }}>
            🔧 <strong>Portfolio Comparison:</strong> In development - framework ready
          </div>
          <div>
            📋 <strong>Predictive Analytics:</strong> Planned - AI model integration coming soon
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div style={{ 
        marginTop: '1rem',
        display: 'flex',
        gap: '1rem',
        flexWrap: 'wrap'
      }}>
        <button 
          onClick={() => window.open(`/api/properties/${propertyId}/availability-calendar?start_date=${new Date(Date.now() - 90*24*60*60*1000).toISOString().split('T')[0]}&end_date=${new Date().toISOString().split('T')[0]}`, '_blank')}
          className="btn btn-secondary"
          style={{ fontSize: '0.875rem' }}
        >
          📊 Raw Calendar Data
        </button>
        
        <button 
          onClick={() => window.open(`/api/properties/${propertyId}/occupancy-stats?days=30`, '_blank')}
          className="btn btn-secondary"
          style={{ fontSize: '0.875rem' }}
        >
          📈 Occupancy Stats
        </button>
        
        <a 
          href="/test-phase2"
          className="btn btn-secondary"
          style={{ fontSize: '0.875rem', textDecoration: 'none' }}
        >
          🧪 Test All Features
        </a>
      </div>
    </div>
  );
};

export default Phase3Analytics;