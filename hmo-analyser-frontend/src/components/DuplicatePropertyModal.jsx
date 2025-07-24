// DuplicatePropertyModal.jsx
import React, { useState } from 'react';
import { X, Home, MapPin, DollarSign, Users, Calendar, AlertTriangle } from 'lucide-react';

const DuplicatePropertyModal = ({ 
  isOpen, 
  onClose, 
  duplicateData, 
  onLinkToExisting, 
  onCreateSeparate,
  isLoading = false 
}) => {
  const [selectedAction, setSelectedAction] = useState(null);

  if (!isOpen || !duplicateData) return null;

  const { potential_matches, extracted_address, new_url } = duplicateData;
  const bestMatch = potential_matches?.[0];

  if (!bestMatch) return null;

  const confidenceColor = bestMatch.confidence_score >= 0.8 ? '#059669' : 
                         bestMatch.confidence_score >= 0.6 ? '#d97706' : '#dc2626';

  const handleAction = async (action) => {
    setSelectedAction(action);
    
    if (action === 'link') {
      await onLinkToExisting(bestMatch.property_id, new_url);
    } else if (action === 'separate') {
      await onCreateSeparate();
    }
    
    setSelectedAction(null);
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '1rem'
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '12px',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        maxWidth: '600px',
        width: '100%',
        maxHeight: '90vh',
        overflowY: 'auto'
      }}>
        {/* Header */}
        <div style={{
          padding: '1.5rem',
          borderBottom: '1px solid #e2e8f0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <AlertTriangle size={24} color="#d97706" />
            <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: '600', color: '#1e293b' }}>
              Potential Duplicate Detected
            </h2>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: '0.5rem',
              borderRadius: '6px',
              color: '#64748b'
            }}
            onMouseOver={(e) => e.target.style.backgroundColor = '#f1f5f9'}
            onMouseOut={(e) => e.target.style.backgroundColor = 'transparent'}
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div style={{ padding: '1.5rem' }}>
          {/* Confidence Score */}
          <div style={{
            backgroundColor: '#f8fafc',
            padding: '1rem',
            borderRadius: '8px',
            marginBottom: '1.5rem',
            border: `2px solid ${confidenceColor}20`
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <div style={{
                width: '12px',
                height: '12px',
                borderRadius: '50%',
                backgroundColor: confidenceColor
              }}></div>
              <span style={{ fontWeight: '600', color: '#1e293b' }}>
                Match Confidence: {(bestMatch.confidence_score * 100).toFixed(1)}%
              </span>
            </div>
            <p style={{ margin: 0, fontSize: '0.875rem', color: '#64748b' }}>
              {bestMatch.confidence_score >= 0.8 
                ? 'Very high confidence - likely the same property'
                : bestMatch.confidence_score >= 0.6 
                ? 'Medium confidence - possibly the same property'
                : 'Lower confidence - may be different properties'}
            </p>
          </div>

          {/* Property Comparison */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
            {/* New Property */}
            <div style={{
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              padding: '1rem'
            }}>
              <h3 style={{ 
                margin: '0 0 0.75rem 0', 
                fontSize: '1rem', 
                fontWeight: '600', 
                color: '#1e293b',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                <Home size={16} />
                New Property
              </h3>
              
              <div style={{ marginBottom: '0.75rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                  <MapPin size={14} color="#64748b" />
                  <span style={{ fontSize: '0.875rem', fontWeight: '500' }}>Address</span>
                </div>
                <p style={{ margin: '0 0 0 1.25rem', fontSize: '0.875rem', color: '#64748b' }}>
                  {extracted_address || 'Address not extracted'}
                </p>
              </div>

              <div style={{ marginBottom: '0.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                  <Calendar size={14} color="#64748b" />
                  <span style={{ fontSize: '0.875rem', fontWeight: '500' }}>Status</span>
                </div>
                <p style={{ margin: '0 0 0 1.25rem', fontSize: '0.875rem', color: '#059669' }}>
                  New listing to analyze
                </p>
              </div>
            </div>

            {/* Existing Property */}
            <div style={{
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              padding: '1rem',
              backgroundColor: '#fafbfc'
            }}>
              <h3 style={{ 
                margin: '0 0 0.75rem 0', 
                fontSize: '1rem', 
                fontWeight: '600', 
                color: '#1e293b',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                <Home size={16} />
                Existing Property
              </h3>
              
              <div style={{ marginBottom: '0.75rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                  <MapPin size={14} color="#64748b" />
                  <span style={{ fontSize: '0.875rem', fontWeight: '500' }}>Address</span>
                </div>
                <p style={{ margin: '0 0 0 1.25rem', fontSize: '0.875rem', color: '#64748b' }}>
                  {bestMatch.address}
                </p>
              </div>

              {bestMatch.property_details?.monthly_income && (
                <div style={{ marginBottom: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                    <DollarSign size={14} color="#64748b" />
                    <span style={{ fontSize: '0.875rem', fontWeight: '500' }}>Monthly Income</span>
                  </div>
                  <p style={{ margin: '0 0 0 1.25rem', fontSize: '0.875rem', color: '#64748b' }}>
                    £{bestMatch.property_details.monthly_income}
                  </p>
                </div>
              )}

              {bestMatch.property_details?.total_rooms && (
                <div style={{ marginBottom: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                    <Users size={14} color="#64748b" />
                    <span style={{ fontSize: '0.875rem', fontWeight: '500' }}>Total Rooms</span>
                  </div>
                  <p style={{ margin: '0 0 0 1.25rem', fontSize: '0.875rem', color: '#64748b' }}>
                    {bestMatch.property_details.total_rooms} rooms
                  </p>
                </div>
              )}

              <div style={{ marginBottom: '0.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                  <Calendar size={14} color="#64748b" />
                  <span style={{ fontSize: '0.875rem', fontWeight: '500' }}>Status</span>
                </div>
                <p style={{ margin: '0 0 0 1.25rem', fontSize: '0.875rem', color: '#0ea5e9' }}>
                  Already in database
                </p>
              </div>
            </div>
          </div>

          {/* Match Factors */}
          {bestMatch.match_factors && (
            <div style={{
              backgroundColor: '#f8fafc',
              padding: '1rem',
              borderRadius: '8px',
              marginBottom: '1.5rem'
            }}>
              <h4 style={{ margin: '0 0 0.75rem 0', fontSize: '0.875rem', fontWeight: '600', color: '#1e293b' }}>
                Match Factors
              </h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '0.5rem' }}>
                {bestMatch.match_factors.address_similarity !== undefined && (
                  <div style={{ fontSize: '0.75rem' }}>
                    <span style={{ color: '#64748b' }}>Address:</span>{' '}
                    <span style={{ fontWeight: '500' }}>{(bestMatch.match_factors.address_similarity * 100).toFixed(0)}%</span>
                  </div>
                )}
                {bestMatch.match_factors.geographic_similarity !== undefined && (
                  <div style={{ fontSize: '0.75rem' }}>
                    <span style={{ color: '#64748b' }}>Location:</span>{' '}
                    <span style={{ fontWeight: '500' }}>{(bestMatch.match_factors.geographic_similarity * 100).toFixed(0)}%</span>
                  </div>
                )}
                {bestMatch.match_factors.price_similarity !== undefined && (
                  <div style={{ fontSize: '0.75rem' }}>
                    <span style={{ color: '#64748b' }}>Price:</span>{' '}
                    <span style={{ fontWeight: '500' }}>{(bestMatch.match_factors.price_similarity * 100).toFixed(0)}%</span>
                  </div>
                )}
                {bestMatch.match_factors.room_count_similarity !== undefined && (
                  <div style={{ fontSize: '0.75rem' }}>
                    <span style={{ color: '#64748b' }}>Rooms:</span>{' '}
                    <span style={{ fontWeight: '500' }}>{(bestMatch.match_factors.room_count_similarity * 100).toFixed(0)}%</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
            <button
              onClick={() => handleAction('separate')}
              disabled={isLoading}
              style={{
                padding: '0.75rem 1.5rem',
                backgroundColor: isLoading && selectedAction === 'separate' ? '#9ca3af' : '#f1f5f9',
                color: isLoading && selectedAction === 'separate' ? '#ffffff' : '#374151',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                fontSize: '0.875rem',
                fontWeight: '500',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}
            >
              {isLoading && selectedAction === 'separate' && (
                <div className="spinner" style={{ width: '16px', height: '16px' }}></div>
              )}
              Add as Separate Property
            </button>

            <button
              onClick={() => handleAction('link')}
              disabled={isLoading}
              style={{
                padding: '0.75rem 1.5rem',
                backgroundColor: isLoading && selectedAction === 'link' ? '#9ca3af' : '#667eea',
                color: '#ffffff',
                border: 'none',
                borderRadius: '6px',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                fontSize: '0.875rem',
                fontWeight: '500',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}
            >
              {isLoading && selectedAction === 'link' && (
                <div className="spinner" style={{ width: '16px', height: '16px' }}></div>
              )}
              🔗 Link to Existing Property
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DuplicatePropertyModal;