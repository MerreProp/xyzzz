import React, { useState, useEffect } from 'react';

const MapUsageStats = ({ tracker }) => {
  const [stats, setStats] = useState(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (!tracker) return;
    
    const updateStats = () => {
      setStats(tracker.getSessionStats());
    };

    // Update stats every 5 seconds
    const interval = setInterval(updateStats, 5000);
    updateStats(); // Initial update

    return () => clearInterval(interval);
  }, [tracker]);

  if (!stats) return null;

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
  };

  return (
    <div style={{
      position: 'fixed',
      bottom: '1rem',
      right: '1rem',
      zIndex: 1000
    }}>
      {/* Toggle Button */}
      <button
        onClick={() => setIsVisible(!isVisible)}
        style={{
          background: '#667eea',
          color: 'white',
          border: 'none',
          borderRadius: '50%',
          width: '48px',
          height: '48px',
          cursor: 'pointer',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          fontSize: '1.25rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
        title="View Map Usage Stats"
      >
        📊
      </button>

      {/* Stats Panel */}
      {isVisible && (
        <div style={{
          position: 'absolute',
          bottom: '60px',
          right: '0',
          background: 'white',
          border: '1px solid #e2e8f0',
          borderRadius: '8px',
          padding: '1rem',
          boxShadow: '0 10px 25px rgba(0,0,0,0.15)',
          minWidth: '240px'
        }}>
          <div style={{ 
            fontSize: '0.875rem', 
            fontWeight: '600', 
            marginBottom: '0.75rem',
            color: '#374151',
            borderBottom: '1px solid #f1f5f9',
            paddingBottom: '0.5rem'
          }}>
            📈 Session Usage Stats
          </div>

          <div style={{ fontSize: '0.75rem', lineHeight: '1.4', color: '#64748b' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span>🗺️ Map Loads:</span>
              <strong style={{ color: stats.mapLoads > 0 ? '#dc2626' : '#059669' }}>
                {stats.mapLoads}
              </strong>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span>🏠 Property Clicks:</span>
              <strong>{stats.interactions}</strong>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span>🔍 Filter Changes:</span>
              <strong>{stats.filters}</strong>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span>⏱️ Session Time:</span>
              <strong>{formatDuration(stats.duration)}</strong>
            </div>

            <div style={{ 
              marginTop: '0.75rem', 
              paddingTop: '0.5rem',
              borderTop: '1px solid #f1f5f9',
              fontSize: '0.7rem',
              color: '#9ca3af'
            }}>
              💡 Map loads count toward Mapbox quota<br/>
              Style changes = new map loads
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MapUsageStats;