import React, { useState, useEffect, useRef } from 'react';

const PropertyForm = ({ onSubmit, isLoading, analysisResult, analysisError }) => {
  const [url, setUrl] = useState('');
  const [notification, setNotification] = useState(null);
  const [hasSubmitted, setHasSubmitted] = useState(false);

  // Clear the form when analysis is completed OR failed
  useEffect(() => {
    if (analysisResult && hasSubmitted) {
      setUrl('');
      setHasSubmitted(false);
      // Clear notification after a delay
      setTimeout(() => setNotification(null), 5000);
    }
  }, [analysisResult, hasSubmitted]);

  // Reset form when analysis fails (when isLoading changes from true to false without result)
  useEffect(() => {
    if (!isLoading && hasSubmitted && !analysisResult) {
      // Analysis likely failed, reset the form
      setHasSubmitted(false);
    }
  }, [isLoading, hasSubmitted, analysisResult]);

  // Reset form when analysisError changes (indicates failure)
  useEffect(() => {
    if (analysisError && hasSubmitted) {
      setHasSubmitted(false);
      setUrl(''); // Clear the URL on error
      // Show error notification
      setNotification({
        type: 'error',
        message: `Analysis failed: ${analysisError}`
      });
    }
  }, [analysisError, hasSubmitted]);

  // Additional effect to clear URL when loading stops (backup method)
  const wasLoading = useRef(false);
  
  useEffect(() => {
    if (isLoading) {
      wasLoading.current = true;
    } else if (wasLoading.current && !isLoading && hasSubmitted) {
      // Analysis finished (either success or failure)
      setTimeout(() => {
        setUrl('');
        setHasSubmitted(false);
      }, 2000); // Small delay to let user see the result
      wasLoading.current = false;
    }
  }, [isLoading, hasSubmitted]);

  const handleSubmit = async (e) => {
    if (e && e.preventDefault) {
      e.preventDefault();
    }
    
    if (!url.trim() || isLoading || !onSubmit) return;

    console.log('handleSubmit called, onSubmit type:', typeof onSubmit); // Debug log

    setHasSubmitted(true);
    
    // Immediately show a "submitting" notification
    setNotification({
      type: 'submitting',
      message: 'Starting analysis...'
    });

    try {
      const result = await onSubmit(url);
      console.log('Analysis result:', result); // Debug log
      
      // Display notification based on whether property exists
      if (result?.property_metadata) {
        setNotification({
          type: result.property_metadata.is_existing ? 'existing' : 'new',
          data: result.property_metadata,
          message: result.message
        });
      } else if (result?.message) {
        // Fallback if no metadata is provided
        setNotification({
          type: 'info',
          message: result.message
        });
      }
    } catch (error) {
      console.error('Analysis error:', error); // Debug log
      setNotification({
        type: 'error',
        message: 'Failed to start analysis. Please try again.'
      });
      setHasSubmitted(false); // Reset form state on error
      // Clear the URL field on error as well
      setUrl('');
    }
  };

  const renderNotification = () => {
    if (!notification) return null;

    const getNotificationStyle = () => {
      switch (notification.type) {
        case 'existing':
          return {
            backgroundColor: '#fef3c7',
            borderColor: '#f59e0b',
            color: '#92400e',
            icon: '🔄'
          };
        case 'new':
          return {
            backgroundColor: '#d1fae5',
            borderColor: '#10b981',
            color: '#047857',
            icon: '✨'
          };
        case 'submitting':
          return {
            backgroundColor: '#dbeafe',
            borderColor: '#3b82f6',
            color: '#1e40af',
            icon: '⏳'
          };
        case 'error':
          return {
            backgroundColor: '#fee2e2',
            borderColor: '#ef4444',
            color: '#dc2626',
            icon: '❌'
          };
        default:
          return {
            backgroundColor: '#e0f2fe',
            borderColor: '#0ea5e9',
            color: '#0c4a6e',
            icon: 'ℹ️'
          };
      }
    };

    const style = getNotificationStyle();

    return (
      <div 
        style={{
          marginTop: '1rem',
          padding: '1rem',
          backgroundColor: style.backgroundColor,
          border: `1px solid ${style.borderColor}`,
          borderRadius: '8px',
          color: style.color,
          animation: 'fadeIn 0.3s ease-in'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
          <span style={{ fontSize: '1.25rem', flexShrink: 0 }}>
            {style.icon}
          </span>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: '600', marginBottom: '0.5rem' }}>
              {notification.type === 'existing' && 'Property Already Analyzed'}
              {notification.type === 'new' && 'New Property Detected'}
              {notification.type === 'submitting' && 'Analysis Starting'}
              {notification.type === 'error' && 'Analysis Failed'}
              {notification.type === 'info' && 'Analysis Update'}
            </div>
            <div style={{ fontSize: '0.875rem', lineHeight: '1.4' }}>
              {notification.message}
            </div>
            
            {notification.data && notification.type === 'existing' && (
              <div style={{ 
                marginTop: '0.75rem', 
                fontSize: '0.8rem',
                backgroundColor: 'rgba(255, 255, 255, 0.5)',
                padding: '0.5rem',
                borderRadius: '4px'
              }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                  <div>
                    <strong>Total Analyses:</strong> {notification.data.total_analyses}
                  </div>
                  <div>
                    <strong>Changes Tracked:</strong> {notification.data.total_changes || 0}
                  </div>
                  {notification.data.last_analyzed && (
                    <div style={{ gridColumn: '1 / -1' }}>
                      <strong>Last Analyzed:</strong> {new Date(notification.data.last_analyzed).toLocaleDateString()}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
          {notification.type !== 'submitting' && (
            <button
              onClick={() => setNotification(null)}
              style={{
                background: 'none',
                border: 'none',
                fontSize: '1.25rem',
                cursor: 'pointer',
                color: 'inherit',
                opacity: 0.7,
                flexShrink: 0
              }}
              onMouseOver={(e) => e.target.style.opacity = '1'}
              onMouseOut={(e) => e.target.style.opacity = '0.7'}
            >
              ×
            </button>
          )}
        </div>
      </div>
    );
  };

  const isValidSpareRoomUrl = (url) => {
    try {
      const urlObj = new URL(url);
      return urlObj.hostname.includes('spareroom.co.uk');
    } catch {
      return false;
    }
  };

  const isValid = url.trim() && isValidSpareRoomUrl(url);
  const buttonDisabled = !isValid || isLoading || hasSubmitted;

  const getButtonStyle = () => {
    if (isLoading || hasSubmitted) {
      return {
        backgroundColor: '#f59e0b', // Orange when loading
        cursor: 'not-allowed',
        transform: 'scale(0.98)' // Slightly smaller when pressed
      };
    } else if (isValid) {
      return {
        backgroundColor: '#3b82f6', // Blue when ready
        cursor: 'pointer',
        transform: 'scale(1)'
      };
    } else {
      return {
        backgroundColor: '#9ca3af', // Gray when disabled
        cursor: 'not-allowed',
        transform: 'scale(1)'
      };
    }
  };

  return (
    <div className="card">
      <style>
        {`
          @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
          }
          
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
          }
          
          .analyzing-pulse {
            animation: pulse 1.5s ease-in-out infinite;
          }
        `}
      </style>
      
      <div className="card-header">
        <h3 className="card-title">🏠 Analyze SpareRoom Property</h3>
        <p className="card-subtitle">
          Enter a SpareRoom URL to analyze HMO investment potential
        </p>
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <div style={{ marginBottom: '1rem' }}>
          <label 
            htmlFor="property-url" 
            style={{ 
              display: 'block', 
              marginBottom: '0.5rem', 
              fontWeight: '500',
              color: '#374151'
            }}
          >
            SpareRoom Property URL
          </label>
          <input
            id="property-url"
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.spareroom.co.uk/flatshare/..."
            disabled={isLoading || hasSubmitted}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && isValid && !buttonDisabled) {
                handleSubmit(e);
              }
            }}
            style={{
              width: '100%',
              padding: '0.75rem',
              border: `2px solid ${(isLoading || hasSubmitted) ? '#f59e0b' : '#d1d5db'}`,
              borderRadius: '6px',
              fontSize: '1rem',
              backgroundColor: (isLoading || hasSubmitted) ? '#fef3c7' : 'white',
              transition: 'all 0.2s ease'
            }}
          />
          {url && !isValidSpareRoomUrl(url) && (
            <p style={{ 
              marginTop: '0.25rem', 
              fontSize: '0.875rem', 
              color: '#ef4444' 
            }}>
              Please enter a valid SpareRoom URL
            </p>
          )}
        </div>

        <button
          onClick={handleSubmit}
          disabled={buttonDisabled}
          className={isLoading || hasSubmitted ? 'analyzing-pulse' : ''}
          style={{
            width: '100%',
            padding: '0.75rem 1.5rem',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            fontSize: '1rem',
            fontWeight: '600',
            transition: 'all 0.2s ease',
            ...getButtonStyle()
          }}
        >
          {isLoading || hasSubmitted ? (
            <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
              <div 
                className="spinner" 
                style={{ 
                  width: '16px', 
                  height: '16px',
                  border: '2px solid rgba(255,255,255,0.3)',
                  borderTop: '2px solid white',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite'
                }}
              ></div>
              {hasSubmitted ? 'Analysis Started...' : 'Analyzing Property...'}
            </span>
          ) : (
            'Start Analysis'
          )}
        </button>
      </div>

      {renderNotification()}

      <div style={{ 
        fontSize: '0.875rem', 
        color: '#6b7280',
        borderTop: '1px solid #e5e7eb',
        paddingTop: '1rem'
      }}>
        <p style={{ margin: 0 }}>
          <strong>Tip:</strong> The system will automatically detect if this property has been analyzed before 
          and show you the analysis history along with any changes detected over time.
        </p>
      </div>
      
      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>
    </div>
  );
};

export default PropertyForm;