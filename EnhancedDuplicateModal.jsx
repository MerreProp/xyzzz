import React, { useState } from 'react';
import { X, MapPin, DollarSign, Home, Users, Calendar, AlertTriangle, Check, ArrowRight, Info } from 'lucide-react';

const EnhancedDuplicateModal = ({ 
  isOpen, 
  onClose, 
  duplicateData, 
  onLinkToExisting, 
  onCreateSeparate,
  isLoading = false 
}) => {
  const [selectedAction, setSelectedAction] = useState(null);
  const [showDetails, setShowDetails] = useState(false);

  if (!isOpen || !duplicateData) return null;

  const { potential_matches, extracted_address, new_url } = duplicateData;
  const bestMatch = potential_matches?.[0];

  if (!bestMatch) return null;

  // Enhanced data from Phase 2
  const distance = bestMatch.distance_meters;
  const proximityLevel = bestMatch.proximity_level || 'unknown';
  const recommendation = bestMatch.recommendation || 'user_choice';
  const confidence = bestMatch.confidence_score || 0;

  const getConfidenceColor = (score) => {
    if (score >= 0.8) return '#059669'; // High - Green
    if (score >= 0.6) return '#d97706'; // Medium - Orange  
    return '#dc2626'; // Low - Red
  };

  const getProximityColor = (level) => {
    const colors = {
      'same_address': '#059669',
      'same_building': '#10b981', 
      'same_block': '#f59e0b',
      'same_street': '#f97316',
      'walking_distance': '#6b7280',
      'same_neighborhood': '#9ca3af',
      'different_area': '#dc2626'
    };
    return colors[level] || '#6b7280';
  };

  const getProximityIcon = (level) => {
    if (['same_address', 'same_building'].includes(level)) return '🏠';
    if (['same_block', 'same_street'].includes(level)) return '🏘️';
    if (['walking_distance', 'same_neighborhood'].includes(level)) return '🚶‍♂️';
    return '🌍';
  };

  const getRecommendationStyle = (rec) => {
    const styles = {
      'auto_link': { bg: '#dcfce7', border: '#16a34a', text: '#15803d', label: '🔗 Auto-Link Recommended' },
      'user_choice': { bg: '#fef3c7', border: '#f59e0b', text: '#d97706', label: '🤔 Your Decision Needed' },
      'separate': { bg: '#fee2e2', border: '#dc2626', text: '#dc2626', label: '🆕 Keep Separate' }
    };
    return styles[rec] || styles.user_choice;
  };

  const handleAction = async (action) => {
    setSelectedAction(action);
    if (action === 'link') {
      await onLinkToExisting();
    } else {
      await onCreateSeparate();
    }
  };

  const recStyle = getRecommendationStyle(recommendation);

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.6)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '1rem'
    }}>
      <div style={{
        backgroundColor: '#ffffff',
        borderRadius: '16px',
        maxWidth: '900px',
        width: '100%',
        maxHeight: '90vh',
        overflow: 'auto',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        animation: 'modalSlideIn 0.3s ease-out'
      }}>
        {/* Header */}
        <div style={{
          padding: '1.5rem',
          borderBottom: '1px solid #e5e7eb',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div>
            <h2 style={{
              fontSize: '1.5rem',
              fontWeight: '700',
              color: '#111827',
              margin: 0,
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              🔍 Potential Duplicate Detected
            </h2>
            <p style={{
              color: '#6b7280',
              margin: '0.25rem 0 0 0',
              fontSize: '0.875rem'
            }}>
              We found a similar property that might be the same one
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              padding: '0.5rem',
              borderRadius: '8px',
              border: 'none',
              backgroundColor: '#f3f4f6',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <X size={20} color="#6b7280" />
          </button>
        </div>

        {/* Recommendation Banner */}
        <div style={{
          margin: '1.5rem',
          padding: '1rem',
          backgroundColor: recStyle.bg,
          border: `2px solid ${recStyle.border}`,
          borderRadius: '12px',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem'
        }}>
          <div style={{
            fontSize: '1.125rem',
            fontWeight: '600',
            color: recStyle.text
          }}>
            {recStyle.label}
          </div>
          <div style={{
            backgroundColor: getConfidenceColor(confidence),
            color: 'white',
            padding: '0.25rem 0.75rem',
            borderRadius: '20px',
            fontSize: '0.875rem',
            fontWeight: '500'
          }}>
            {(confidence * 100).toFixed(0)}% Confidence
          </div>
        </div>

        {/* Side-by-Side Comparison */}
        <div style={{
          padding: '0 1.5rem',
          display: 'grid',
          gridTemplateColumns: '1fr auto 1fr',
          gap: '1.5rem',
          alignItems: 'start'
        }}>
          {/* Existing Property */}
          <div style={{
            padding: '1.25rem',
            backgroundColor: '#f8fafc',
            borderRadius: '12px',
            border: '2px solid #e2e8f0'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              marginBottom: '1rem'
            }}>
              <Home size={20} color="#475569" />
              <h3 style={{
                fontSize: '1.125rem',
                fontWeight: '600',
                color: '#334155',
                margin: 0
              }}>
                Existing Property
              </h3>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <div style={{
                fontSize: '0.875rem',
                color: '#64748b',
                marginBottom: '0.25rem'
              }}>
                Address
              </div>
              <div style={{
                fontWeight: '500',
                color: '#1e293b',
                lineHeight: '1.4'
              }}>
                {bestMatch.address}
              </div>
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '1rem',
              marginBottom: '1rem'
            }}>
              <div>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Monthly Income</div>
                <div style={{ fontWeight: '600', color: '#059669' }}>
                  £{bestMatch.property_details?.monthly_income || 'Unknown'}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Total Rooms</div>
                <div style={{ fontWeight: '600' }}>
                  {bestMatch.property_details?.total_rooms || 'Unknown'}
                </div>
              </div>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Advertiser</div>
              <div style={{ fontWeight: '500' }}>
                {bestMatch.property_details?.advertiser_name || 'Unknown'}
              </div>
            </div>

            <div>
              <div style={{ fontSize: '0.75rem', color: '#64748b' }}>First Seen</div>
              <div style={{ fontSize: '0.875rem' }}>
                {bestMatch.property_details?.created_at 
                  ? new Date(bestMatch.property_details.created_at).toLocaleDateString()
                  : 'Unknown'
                }
              </div>
            </div>
          </div>

          {/* Distance & Proximity Indicator */}
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '0.75rem',
            padding: '1rem 0'
          }}>
            <div style={{
              backgroundColor: getProximityColor(proximityLevel),
              color: 'white',
              padding: '0.75rem',
              borderRadius: '50%',
              fontSize: '1.5rem',
              width: '60px',
              height: '60px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              {getProximityIcon(proximityLevel)}
            </div>

            {distance && (
              <div style={{ textAlign: 'center' }}>
                <div style={{
                  fontSize: '1.25rem',
                  fontWeight: '700',
                  color: getProximityColor(proximityLevel)
                }}>
                  {distance < 1000 
                    ? `${Math.round(distance)}m`
                    : `${(distance/1000).toFixed(1)}km`
                  }
                </div>
                <div style={{
                  fontSize: '0.75rem',
                  color: '#6b7280',
                  textTransform: 'capitalize'
                }}>
                  {proximityLevel.replace('_', ' ')}
                </div>
              </div>
            )}

            <ArrowRight size={20} color="#9ca3af" />
          </div>

          {/* New Property */}
          <div style={{
            padding: '1.25rem',
            backgroundColor: '#fefbf3',
            borderRadius: '12px',
            border: '2px solid #fed7aa'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              marginBottom: '1rem'
            }}>
              <Home size={20} color="#ea580c" />
              <h3 style={{
                fontSize: '1.125rem',
                fontWeight: '600',
                color: '#c2410c',
                margin: 0
              }}>
                New Property
              </h3>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <div style={{
                fontSize: '0.875rem',
                color: '#92400e',
                marginBottom: '0.25rem'
              }}>
                Address
              </div>
              <div style={{
                fontWeight: '500',
                color: '#451a03',
                lineHeight: '1.4'
              }}>
                {extracted_address || 'Extracting...'}
              </div>
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '1rem',
              marginBottom: '1rem'
            }}>
              <div>
                <div style={{ fontSize: '0.75rem', color: '#92400e' }}>Status</div>
                <div style={{ fontWeight: '600', color: '#ea580c' }}>
                  New Discovery
                </div>
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', color: '#92400e' }}>Analysis</div>
                <div style={{ fontWeight: '600' }}>
                  Pending
                </div>
              </div>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.75rem', color: '#92400e' }}>Source URL</div>
              <div style={{ 
                fontSize: '0.75rem',
                color: '#451a03',
                wordBreak: 'break-all',
                fontFamily: 'monospace'
              }}>
                {new_url.substring(0, 50)}...
              </div>
            </div>
          </div>
        </div>

        {/* Confidence Breakdown */}
        <div style={{ padding: '1.5rem' }}>
          <button
            onClick={() => setShowDetails(!showDetails)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              backgroundColor: 'transparent',
              border: 'none',
              cursor: 'pointer',
              fontSize: '0.875rem',
              fontWeight: '500',
              color: '#4f46e5',
              marginBottom: showDetails ? '1rem' : '0'
            }}
          >
            <Info size={16} />
            {showDetails ? 'Hide' : 'Show'} Confidence Details
          </button>

          {showDetails && bestMatch.match_factors && (
            <div style={{
              backgroundColor: '#f8fafc',
              padding: '1rem',
              borderRadius: '8px',
              border: '1px solid #e2e8f0'
            }}>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '1rem'
              }}>
                {bestMatch.match_factors.address_similarity !== undefined && (
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Address Match</div>
                    <div style={{ fontWeight: '600' }}>
                      {(bestMatch.match_factors.address_similarity * 100).toFixed(0)}%
                    </div>
                  </div>
                )}

                {bestMatch.match_factors.geographic_similarity !== undefined && (
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Location Match</div>
                    <div style={{ fontWeight: '600' }}>
                      {(bestMatch.match_factors.geographic_similarity * 100).toFixed(0)}%
                    </div>
                  </div>
                )}

                {bestMatch.match_factors.price_similarity !== undefined && (
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Price Match</div>
                    <div style={{ fontWeight: '600' }}>
                      {(bestMatch.match_factors.price_similarity * 100).toFixed(0)}%
                    </div>
                  </div>
                )}

                {bestMatch.match_factors.advertiser_similarity !== undefined && (
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Landlord Match</div>
                    <div style={{ fontWeight: '600' }}>
                      {(bestMatch.match_factors.advertiser_similarity * 100).toFixed(0)}%
                    </div>
                  </div>
                )}
              </div>

              {/* Phase 2 proximity adjustments */}
              {bestMatch.match_factors.proximity_adjustments && (
                <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.5rem' }}>
                    Proximity Adjustments:
                  </div>
                  {bestMatch.match_factors.proximity_adjustments.adjustments_applied?.map((adj, idx) => (
                    <div key={idx} style={{
                      fontSize: '0.75rem',
                      color: adj.boost ? '#059669' : '#dc2626',
                      marginBottom: '0.25rem'
                    }}>
                      • {adj.reason} ({adj.boost ? `+${(adj.boost * 100).toFixed(0)}%` : `-${(adj.penalty * 100).toFixed(0)}%`})
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div style={{
          padding: '1.5rem',
          borderTop: '1px solid #e5e7eb',
          display: 'flex',
          gap: '0.75rem',
          justifyContent: 'flex-end'
        }}>
          <button
            onClick={() => handleAction('separate')}
            disabled={isLoading}
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: isLoading && selectedAction === 'separate' ? '#9ca3af' : '#f1f5f9',
              color: isLoading && selectedAction === 'separate' ? '#ffffff' : '#374151',
              border: '1px solid #d1d5db',
              borderRadius: '8px',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              fontSize: '0.875rem',
              fontWeight: '500',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}
          >
            {isLoading && selectedAction === 'separate' && (
              <div style={{
                width: '16px',
                height: '16px',
                border: '2px solid #ffffff',
                borderTop: '2px solid transparent',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite'
              }}></div>
            )}
            🆕 Keep as Separate Property
          </button>

          <button
            onClick={() => handleAction('link')}
            disabled={isLoading}
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: isLoading && selectedAction === 'link' ? '#9ca3af' : '#4f46e5',
              color: '#ffffff',
              border: 'none',
              borderRadius: '8px',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              fontSize: '0.875rem',
              fontWeight: '500',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}
          >
            {isLoading && selectedAction === 'link' && (
              <div style={{
                width: '16px',
                height: '16px',
                border: '2px solid #ffffff',
                borderTop: '2px solid transparent',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite'
              }}></div>
            )}
            🔗 Link to Existing Property
          </button>
        </div>
      </div>

      <style>{`
        @keyframes modalSlideIn {
          from {
            opacity: 0;
            transform: translateY(-50px) scale(0.95);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }
        
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default EnhancedDuplicateModal;