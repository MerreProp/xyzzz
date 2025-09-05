// EnhancedDuplicateModal.jsx
// Copy this file to: src/components/EnhancedDuplicateModal.jsx

import React, { useState } from 'react';
import { X, MapPin, DollarSign, Home, Users, Calendar, AlertTriangle, Check, ArrowRight, Info, Building } from 'lucide-react';

const EnhancedDuplicateModal = ({ 
  isOpen, 
  onClose, 
  duplicateData, 
  onLinkToExisting, 
  onCreateSeparate,
  onAddSeparateRoom, // NEW FUNCTION for separate room scenario
  isLoading = false 
}) => {
  const [selectedAction, setSelectedAction] = useState(null);
  const [showDetails, setShowDetails] = useState(false);

  if (!isOpen || !duplicateData) return null;

  const { potential_matches, extracted_address, new_url } = duplicateData;
  const bestMatch = potential_matches?.[0];

  if (!bestMatch) return null;

  const distance = bestMatch.distance_meters;
  const proximityLevel = bestMatch.proximity_level || 'unknown';
  const confidence = bestMatch.confidence_score || 0;

  const getConfidenceColor = (score) => {
    if (score >= 0.8) return '#059669';
    if (score >= 0.6) return '#d97706';
    return '#dc2626';
  };

  const getProximityIcon = (level) => {
    if (['same_address', 'same_building'].includes(level)) return '🏠';
    if (['same_block', 'same_street'].includes(level)) return '🏘️';
    if (['walking_distance', 'same_neighborhood'].includes(level)) return '🚶‍♂️';
    return '🌍';
  };

  const formatDistance = (meters) => {
    if (!meters) return 'Unknown distance';
    if (meters < 1000) return `${Math.round(meters)}m away`;
    return `${(meters / 1000).toFixed(1)}km away`;
  };

  const handleAction = async (action) => {
    setSelectedAction(action);
    
    try {
      if (action === 'duplicate') {
        // Same property - link URLs
        await onLinkToExisting(bestMatch.property_id, new_url);
      } else if (action === 'separate_room') {
        // Separate room in same building
        if (onAddSeparateRoom) {
          await onAddSeparateRoom(bestMatch.property_id, new_url);
        } else {
          // Fallback to separate property if handler not implemented
          await onCreateSeparate();
        }
      } else if (action === 'separate_property') {
        // Completely different property
        await onCreateSeparate();
      }
    } catch (error) {
      console.error('Action failed:', error);
    } finally {
      setSelectedAction(null);
    }
  };

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
        maxWidth: '1000px',
        width: '100%',
        maxHeight: '90vh',
        overflow: 'auto',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)'
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
              🔍 Potential Match Detected
            </h2>
            <p style={{
              color: '#6b7280',
              margin: '0.25rem 0 0 0',
              fontSize: '0.875rem'
            }}>
              We found a similar property. Is this the same property or a different room?
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              padding: '0.5rem',
              borderRadius: '8px',
              border: 'none',
              backgroundColor: '#f3f4f6',
              cursor: 'pointer'
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Confidence Badge */}
        <div style={{
          padding: '1.5rem 1.5rem 0 1.5rem'
        }}>
          <div style={{
            backgroundColor: getConfidenceColor(confidence) + '20',
            border: `2px solid ${getConfidenceColor(confidence)}`,
            borderRadius: '12px',
            padding: '1rem',
            display: 'flex',
            alignItems: 'center',
            gap: '1rem'
          }}>
            <div style={{
              fontSize: '2rem'
            }}>
              {getProximityIcon(proximityLevel)}
            </div>
            <div>
              <div style={{
                fontSize: '1.1rem',
                fontWeight: '600',
                color: getConfidenceColor(confidence)
              }}>
                {(confidence * 100).toFixed(1)}% Match Confidence
              </div>
              <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                {formatDistance(distance)} • {proximityLevel?.replace('_', ' ')}
              </div>
            </div>
          </div>
        </div>

        {/* Comparison Section */}
        <div style={{ padding: '1.5rem' }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '1.5rem',
            marginBottom: '2rem'
          }}>
            {/* Existing Property */}
            <div style={{
              backgroundColor: '#f8fafc',
              padding: '1.5rem',
              borderRadius: '12px',
              border: '2px solid #e2e8f0'
            }}>
              <h3 style={{
                margin: '0 0 1rem 0',
                fontSize: '1.1rem',
                fontWeight: '600',
                color: '#1e293b',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                <Building size={20} />
                Existing Property
              </h3>

              <div style={{ marginBottom: '1rem' }}>
                <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '0.25rem' }}>
                  Address
                </div>
                <div style={{ fontWeight: '500', lineHeight: '1.4' }}>
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
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>In Database Since</div>
                <div style={{ fontSize: '0.875rem' }}>
                  {bestMatch.property_details?.created_at 
                    ? new Date(bestMatch.property_details.created_at).toLocaleDateString()
                    : 'Unknown'}
                </div>
              </div>
            </div>

            {/* New Property */}
            <div style={{
              backgroundColor: '#fefdf8',
              padding: '1.5rem',
              borderRadius: '12px',
              border: '2px solid #fbbf24'
            }}>
              <h3 style={{
                margin: '0 0 1rem 0',
                fontSize: '1.1rem',
                fontWeight: '600',
                color: '#1e293b',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                <Users size={20} />
                New Listing
              </h3>

              <div style={{ marginBottom: '1rem' }}>
                <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '0.25rem' }}>
                  URL Source
                </div>
                <div style={{ 
                  fontWeight: '500', 
                  lineHeight: '1.4',
                  fontSize: '0.875rem',
                  wordBreak: 'break-all'
                }}>
                  {new_url}
                </div>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '0.25rem' }}>
                  Extracted Address
                </div>
                <div style={{ fontWeight: '500', lineHeight: '1.4' }}>
                  {extracted_address || 'Not extracted yet'}
                </div>
              </div>

              <div style={{
                backgroundColor: '#fff7ed',
                padding: '0.75rem',
                borderRadius: '8px',
                fontSize: '0.875rem',
                color: '#9a3412'
              }}>
                📝 This listing will be analyzed to extract full details
              </div>
            </div>
          </div>

          {/* Decision Question */}
          <div style={{
            backgroundColor: '#f0f9ff',
            padding: '1.5rem',
            borderRadius: '12px',
            border: '2px solid #0ea5e9',
            marginBottom: '2rem'
          }}>
            <h3 style={{
              margin: '0 0 1rem 0',
              fontSize: '1.1rem',
              fontWeight: '600',
              color: '#0c4a6e'
            }}>
              ❓ What is this new listing?
            </h3>
            <p style={{
              margin: '0',
              fontSize: '0.875rem',
              color: '#075985',
              lineHeight: '1.5'
            }}>
              Based on the similarity, please choose what this new listing represents:
            </p>
          </div>

          {/* Action Buttons */}
          <div style={{ 
            display: 'flex', 
            flexDirection: 'column',
            gap: '1rem'
          }}>
            {/* Same Property Button */}
            <button
              onClick={() => handleAction('duplicate')}
              disabled={isLoading}
              style={{
                padding: '1rem 1.5rem',
                backgroundColor: isLoading && selectedAction === 'duplicate' ? '#9ca3af' : '#059669',
                color: '#ffffff',
                border: 'none',
                borderRadius: '12px',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                fontSize: '1rem',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                transition: 'all 0.2s'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <Building size={20} />
                <div style={{ textAlign: 'left' }}>
                  <div>🔗 Same Property (Different Listing)</div>
                  <div style={{ fontSize: '0.875rem', opacity: 0.9 }}>
                    Link this URL to the existing property in our database
                  </div>
                </div>
              </div>
              {isLoading && selectedAction === 'duplicate' ? (
                <div style={{
                  width: '20px',
                  height: '20px',
                  border: '2px solid #ffffff',
                  borderTop: '2px solid transparent',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite'
                }} />
              ) : (
                <ArrowRight size={20} />
              )}
            </button>

            {/* Separate Room Button */}
            <button
              onClick={() => handleAction('separate_room')}
              disabled={isLoading}
              style={{
                padding: '1rem 1.5rem',
                backgroundColor: isLoading && selectedAction === 'separate_room' ? '#9ca3af' : '#d97706',
                color: '#ffffff',
                border: 'none',
                borderRadius: '12px',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                fontSize: '1rem',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                transition: 'all 0.2s'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <Users size={20} />
                <div style={{ textAlign: 'left' }}>
                  <div>🏠 Separate Room (Same Building)</div>
                  <div style={{ fontSize: '0.875rem', opacity: 0.9 }}>
                    Different room within the same property/building we've already analyzed
                  </div>
                </div>
              </div>
              {isLoading && selectedAction === 'separate_room' ? (
                <div style={{
                  width: '20px',
                  height: '20px',
                  border: '2px solid #ffffff',
                  borderTop: '2px solid transparent',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite'
                }} />
              ) : (
                <ArrowRight size={20} />
              )}
            </button>

            {/* Completely Separate Button */}
            <button
              onClick={() => handleAction('separate_property')}
              disabled={isLoading}
              style={{
                padding: '1rem 1.5rem',
                backgroundColor: isLoading && selectedAction === 'separate_property' ? '#9ca3af' : '#6b7280',
                color: '#ffffff',
                border: 'none',
                borderRadius: '12px',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                fontSize: '1rem',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                transition: 'all 0.2s'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <Home size={20} />
                <div style={{ textAlign: 'left' }}>
                  <div>🆕 Completely Different Property</div>
                  <div style={{ fontSize: '0.875rem', opacity: 0.9 }}>
                    This is a different property entirely, create separate analysis
                  </div>
                </div>
              </div>
              {isLoading && selectedAction === 'separate_property' ? (
                <div style={{
                  width: '20px',
                  height: '20px',
                  border: '2px solid #ffffff',
                  borderTop: '2px solid transparent',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite'
                }} />
              ) : (
                <ArrowRight size={20} />
              )}
            </button>
          </div>

          {/* Match Details Toggle */}
          <div style={{ marginTop: '1.5rem' }}>
            <button
              onClick={() => setShowDetails(!showDetails)}
              style={{
                padding: '0.75rem',
                backgroundColor: '#f8fafc',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '0.875rem',
                color: '#64748b',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}
            >
              <Info size={16} />
              {showDetails ? 'Hide' : 'Show'} Match Details
            </button>

            {showDetails && (
              <div style={{
                marginTop: '1rem',
                backgroundColor: '#f8fafc',
                padding: '1rem',
                borderRadius: '8px',
                fontSize: '0.875rem'
              }}>
                <h4 style={{ margin: '0 0 0.75rem 0', fontWeight: '600' }}>
                  Match Factors
                </h4>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '0.5rem' }}>
                  {bestMatch.match_factors?.address_similarity && (
                    <div>
                      <span style={{ color: '#64748b' }}>Address:</span>{' '}
                      <span style={{ fontWeight: '500' }}>{(bestMatch.match_factors.address_similarity * 100).toFixed(0)}%</span>
                    </div>
                  )}
                  {bestMatch.match_factors?.geographic_similarity && (
                    <div>
                      <span style={{ color: '#64748b' }}>Location:</span>{' '}
                      <span style={{ fontWeight: '500' }}>{(bestMatch.match_factors.geographic_similarity * 100).toFixed(0)}%</span>
                    </div>
                  )}
                  {bestMatch.match_factors?.price_similarity && (
                    <div>
                      <span style={{ color: '#64748b' }}>Price:</span>{' '}
                      <span style={{ fontWeight: '500' }}>{(bestMatch.match_factors.price_similarity * 100).toFixed(0)}%</span>
                    </div>
                  )}
                  {bestMatch.match_factors?.room_count_similarity && (
                    <div>
                      <span style={{ color: '#64748b' }}>Rooms:</span>{' '}
                      <span style={{ fontWeight: '500' }}>{(bestMatch.match_factors.room_count_similarity * 100).toFixed(0)}%</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* CSS Animations */}
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default EnhancedDuplicateModal;