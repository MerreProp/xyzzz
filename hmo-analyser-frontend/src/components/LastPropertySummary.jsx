// LastPropertySummary.jsx - Enhanced version with professional changes display and animations

import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { propertyApi } from '../utils/api';
import { useLastUpdateSummary } from '../hooks/useAnalysis';
import { BarChart3, FileText, ExternalLink } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { useDarkMode } from '../contexts/DarkModeContext';

const ChangeCard = ({ change, index }) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), index * 100);
    return () => clearTimeout(timer);
  }, [index]);

  const getChangeIcon = (type) => {
    switch (type) {
      case 'status_change': return '🔄';
      case 'price_change': return '💰';
      case 'room_available': return '✅';
      case 'room_unavailable': return '❌';
      case 'room_became_available': return '🟢';
      case 'room_became_unavailable': return '🔴';
      default: return '📝';
    }
  };

  const getChangeColor = (type) => {
    switch (type) {
      case 'price_change': return { bg: '#fef3c7', border: '#f59e0b', text: '#92400e' };
      case 'room_available': 
      case 'room_became_available': return { bg: '#dcfce7', border: '#16a34a', text: '#166534' };
      case 'room_unavailable':
      case 'room_became_unavailable': return { bg: '#fee2e2', border: '#dc2626', text: '#991b1b' };
      case 'status_change': return { bg: '#e0f2fe', border: '#0284c7', text: '#075985' };
      default: return { bg: '#f1f5f9', border: '#64748b', text: '#475569' };
    }
  };

  const formatChangeDetails = (change) => {
    if (change.type === 'price_change') {
      const oldPrice = change.old_value ? `£${Number(change.old_value).toLocaleString()}` : 'N/A';
      const newPrice = change.new_value ? `£${Number(change.new_value).toLocaleString()}` : 'N/A';
      const diff = change.old_value && change.new_value ? 
        Number(change.new_value) - Number(change.old_value) : 0;
      const diffText = diff > 0 ? `+£${diff.toLocaleString()}` : `£${diff.toLocaleString()}`;
      const diffColor = diff > 0 ? '#dc2626' : '#16a34a';
      
      return (
        <div>
          <div style={{ fontWeight: '600', marginBottom: '4px' }}>
            {change.room_number || 'Room'} - Price Change
          </div>
          <div style={{ fontSize: '0.875rem', color: '#64748b' }}>
            {oldPrice} → {newPrice}
            {diff !== 0 && (
              <span style={{ color: diffColor, fontWeight: '500', marginLeft: '8px' }}>
                ({diffText})
              </span>
            )}
          </div>
        </div>
      );
    }

    if (change.type === 'status_change') {
      return (
        <div>
          <div style={{ fontWeight: '600', marginBottom: '4px' }}>
            Property Status Change
          </div>
          <div style={{ fontSize: '0.875rem', color: '#64748b' }}>
            {change.old_value || 'Unknown'} → {change.new_value || 'Unknown'}
          </div>
        </div>
      );
    }

    if (change.type.includes('available')) {
      const isBecomingAvailable = change.type.includes('became_available') || change.type === 'room_available';
      return (
        <div>
          <div style={{ fontWeight: '600', marginBottom: '4px' }}>
            {change.room_number || 'Room'} - {isBecomingAvailable ? 'Now Available' : 'No Longer Available'}
          </div>
          <div style={{ fontSize: '0.875rem', color: '#64748b' }}>
            {change.summary || (isBecomingAvailable ? 'Room became available for booking' : 'Room is no longer available')}
          </div>
        </div>
      );
    }

    return (
      <div>
        <div style={{ fontWeight: '600', marginBottom: '4px' }}>
          {change.room_number || change.type.replace('_', ' ').toUpperCase()}
        </div>
        <div style={{ fontSize: '0.875rem', color: '#64748b' }}>
          {change.summary || change.change_summary || 'Change detected'}
        </div>
      </div>
    );
  };

  const colors = getChangeColor(change.type);

  return (
    <div 
      style={{
        backgroundColor: colors.bg,
        border: `1px solid ${colors.border}`,
        borderRadius: '8px',
        padding: '12px',
        transition: 'all 0.3s ease',
        transform: isVisible ? 'translateY(0)' : 'translateY(20px)',
        opacity: isVisible ? 1 : 0,
        marginBottom: '8px'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
        <span style={{ fontSize: '1.2rem', marginTop: '2px' }}>
          {getChangeIcon(change.type)}
        </span>
        <div style={{ flex: 1, color: colors.text }}>
          {formatChangeDetails(change)}
          {change.detected_at && (
            <div style={{ 
              fontSize: '0.75rem', 
              color: '#94a3b8', 
              marginTop: '4px',
              fontStyle: 'italic'
            }}>
              {new Date(change.detected_at).toLocaleString('en-GB')}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const UpdateResultsSection = ({ lastUpdateSummary, isExpanded, setIsExpanded }) => {
  const [shouldAnimate, setShouldAnimate] = useState(false);

  useEffect(() => {
    if (isExpanded) {
      setShouldAnimate(true);
    }
  }, [isExpanded]);

  if (!lastUpdateSummary) return null;

  const {
    completed_at,
    total_properties_updated,
    total_changes_detected,
    status_changes = [],
    price_changes = [],
    unavailable_properties = [],
    other_changes = []
  } = lastUpdateSummary;

  // Filter changes to only show the ones you care about
  const relevantChanges = [
    ...status_changes.map(change => ({ ...change, type: 'status_change' })),
    ...price_changes.map(change => ({ ...change, type: 'price_change' })),
    ...other_changes.filter(change => 
      change.change_type === 'room_became_available' || 
      change.change_type === 'room_became_unavailable' ||
      change.change_type === 'room_available' ||
      change.change_type === 'room_unavailable'
    ).map(change => ({ ...change, type: change.change_type }))
  ];

  const formatDateTime = (dateString) => {
    try {
      return new Date(dateString).toLocaleString('en-GB', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString;
    }
  };

  return (
    <div style={{ 
      marginBottom: '1.5rem',
      border: '1px solid #e2e8f0',
      borderRadius: '12px',
      backgroundColor: '#ffffff',
      boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
      overflow: 'hidden'
    }}>
      {/* Header */}
      <div 
        onClick={() => setIsExpanded(!isExpanded)}
        style={{
          padding: '1.25rem 1.5rem',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          backgroundColor: isExpanded ? '#f8fafc' : '#ffffff',
          borderBottom: isExpanded ? '1px solid #e2e8f0' : 'none',
          transition: 'all 0.3s ease'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ 
            width: '40px', 
            height: '40px', 
            borderRadius: '50%', 
            backgroundColor: '#3b82f6',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.2rem'
          }}>
            📊
          </div>
          <div>
            <h3 style={{ 
              margin: 0, 
              fontSize: '1.1rem', 
              fontWeight: '600',
              color: '#1e293b' 
            }}>
              Last Update Results
            </h3>
            <p style={{ 
              margin: 0, 
              fontSize: '0.875rem', 
              color: '#64748b' 
            }}>
              {formatDateTime(completed_at)} • {total_properties_updated} properties updated
            </p>
          </div>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {relevantChanges.length > 0 && (
            <div style={{
              backgroundColor: '#fee2e2',
              color: '#dc2626',
              padding: '4px 12px',
              borderRadius: '20px',
              fontSize: '0.875rem',
              fontWeight: '500'
            }}>
              {relevantChanges.length} change{relevantChanges.length !== 1 ? 's' : ''}
            </div>
          )}
          <div style={{
            transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: 'transform 0.3s ease',
            fontSize: '1.4rem',
            color: '#64748b'
          }}>
            ▼
          </div>
        </div>
      </div>

      {/* Expanded Content with Slide Down Animation */}
      <div style={{
        maxHeight: isExpanded ? '800px' : '0',
        overflow: 'hidden',
        transition: 'max-height 0.4s ease-in-out',
      }}>
        <div style={{ 
          padding: '1.5rem',
          backgroundColor: '#ffffff'
        }}>
          
          {/* Summary Stats */}
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', 
            gap: '1rem',
            marginBottom: '1.5rem'
          }}>
            <div style={{ 
              textAlign: 'center',
              padding: '1rem',
              backgroundColor: '#f8fafc',
              borderRadius: '8px',
              border: '1px solid #e2e8f0'
            }}>
              <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: '#3b82f6' }}>
                {total_properties_updated}
              </div>
              <div style={{ fontSize: '0.875rem', color: '#64748b' }}>Properties</div>
            </div>
            
            <div style={{ 
              textAlign: 'center',
              padding: '1rem',
              backgroundColor: relevantChanges.length > 0 ? '#fef3c7' : '#f0fdf4',
              borderRadius: '8px',
              border: `1px solid ${relevantChanges.length > 0 ? '#f59e0b' : '#16a34a'}`
            }}>
              <div style={{ 
                fontSize: '1.8rem', 
                fontWeight: 'bold', 
                color: relevantChanges.length > 0 ? '#d97706' : '#16a34a'
              }}>
                {relevantChanges.length}
              </div>
              <div style={{ fontSize: '0.875rem', color: '#64748b' }}>Key Changes</div>
            </div>
          </div>

          {/* Changes Display */}
          {relevantChanges.length > 0 ? (
            <div>
              <h4 style={{ 
                fontSize: '1rem', 
                fontWeight: '600', 
                marginBottom: '1rem',
                color: '#1e293b',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                🔍 Important Changes Detected
                <span style={{ 
                  fontSize: '0.75rem', 
                  fontWeight: '400', 
                  color: '#64748b',
                  backgroundColor: '#f1f5f9',
                  padding: '2px 8px',
                  borderRadius: '12px'
                }}>
                  Status • Price • Availability
                </span>
              </h4>
              
              <div style={{ 
                maxHeight: '400px', 
                overflowY: 'auto',
                padding: '4px'
              }}>
                {relevantChanges.map((change, index) => (
                  <ChangeCard 
                    key={`${change.type}-${index}`} 
                    change={change} 
                    index={index}
                  />
                ))}
              </div>
            </div>
          ) : (
            <div style={{
              textAlign: 'center',
              padding: '2rem',
              backgroundColor: '#f0fdf4',
              borderRadius: '8px',
              border: '1px solid #16a34a'
            }}>
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>✅</div>
              <h4 style={{ color: '#166534', marginBottom: '0.5rem', fontSize: '1rem' }}>
                No Important Changes
              </h4>
              <p style={{ 
                color: '#16a34a', 
                fontSize: '0.875rem',
                margin: 0
              }}>
                All properties remain stable. No status, price, or availability changes detected.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const LastPropertySummary = () => {
  const [showUpdateResults, setShowUpdateResults] = useState(false);

  // ADD THESE LINES HERE:
  const { currentPalette } = useTheme();
  const { isDarkMode } = useDarkMode();

  // Use the same theme as main component
  const baseColors = {
    darkSlate: '#2C3E4A',
    lightCream: '#F5F1E8',
    softGray: '#A8A5A0',
  };

  const theme = isDarkMode ? {
    mainBg: '#1a2b32',
    cardBg: '#2c3e4a',
    text: baseColors.lightCream,
    textSecondary: '#9ca3af',
    border: 'rgba(180, 180, 180, 0.2)',
    accent: currentPalette.primary,
    accentHover: currentPalette.secondary
  } : {
    mainBg: baseColors.lightCream,
    cardBg: '#ffffff',
    text: baseColors.darkSlate,
    textSecondary: baseColors.softGray,
    border: 'rgba(168, 165, 160, 0.3)',
    accent: currentPalette.accent,
    accentHover: currentPalette.primary
  };

  // Fetch all properties to get the most recent one
  const { data: properties = [], isLoading, error } = useQuery({
    queryKey: ['properties-last'],
    queryFn: propertyApi.getAllProperties,
  });

  // Fetch last update summary
  const { data: lastUpdateSummary, isLoading: summaryLoading } = useLastUpdateSummary();

  // Helper functions
  const formatCurrency = (amount) => {
    if (!amount) return 'N/A';
    return `£${Number(amount).toLocaleString()}`;
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    
    try {
      let date;
      
      if (typeof dateString === 'string' && dateString.includes('/')) {
        const parts = dateString.split('/');
        if (parts.length === 3) {
          const day = parseInt(parts[0], 10);
          const month = parseInt(parts[1], 10) - 1;
          let year = parseInt(parts[2], 10);
          
          if (year < 100) {
            year += 2000;
          }
          
          date = new Date(year, month, day);
        } else {
          date = new Date(dateString);
        }
      } else {
        date = new Date(dateString);
      }
      
      if (isNaN(date.getTime())) {
        return 'Invalid Date';
      }
      
      return date.toLocaleDateString('en-GB', {
        day: '2-digit',
        month: '2-digit',
        year: '2-digit'
      });
    } catch (error) {
      return 'Invalid Date';
    }
  };

  const formatAvailableRooms = (availableRoomsDetails, availableRooms, property) => {
    // Use room history data if available
    if (property && property['Rooms With History'] && property['Rooms With History'].length > 0) {
      const availableRoomsWithHistory = property['Rooms With History'].filter(
        room => room.current_status === 'available'
      );
      
      if (availableRoomsWithHistory.length === 0) {
        return (
          <div style={{ color: '#dc2626', fontWeight: '500' }}>
            No rooms available
          </div>
        );
      }
      
      return (
        <div>
          <div style={{ fontWeight: '500', marginBottom: '4px' }}>
            {availableRoomsWithHistory.length} room{availableRoomsWithHistory.length !== 1 ? 's' : ''} available
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
            {availableRoomsWithHistory.slice(0, 3).map(room => room.room_number).join(', ')}
            {availableRoomsWithHistory.length > 3 && ` +${availableRoomsWithHistory.length - 3} more`}
          </div>
        </div>
      );
    }
    
    // Fallback to original logic
    if (availableRoomsDetails && availableRoomsDetails.length > 0) {
      return (
        <div>
          <div style={{ fontWeight: '500', marginBottom: '4px' }}>
            {availableRoomsDetails.length} room{availableRoomsDetails.length !== 1 ? 's' : ''} available
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
            {availableRoomsDetails.slice(0, 3).join(', ')}
            {availableRoomsDetails.length > 3 && ` +${availableRoomsDetails.length - 3} more`}
          </div>
        </div>
      );
    }
    
    if (availableRooms) {
      return (
        <div style={{ fontWeight: '500' }}>
          {availableRooms} room{availableRooms !== 1 ? 's' : ''} available
        </div>
      );
    }
    
    return (
      <div style={{ color: '#dc2626', fontWeight: '500' }}>
        No rooms available
      </div>
    );
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'live': 
      case 'active':
        return { bg: '#dcfce7', color: '#166534' };
      case 'offline':
      case 'inactive':
        return { bg: '#fee2e2', color: '#991b1b' };
      case 'pending':
        return { bg: '#fef3c7', color: '#92400e' };
      default:
        return { bg: '#f1f5f9', color: '#475569' };
    }
  };

  // Get the most recent property (sort by analysis_date)
  const lastProperty = React.useMemo(() => {
    if (!properties.length) return null;
    
    return [...properties].sort((a, b) => {
      const aDate = new Date(a.analysis_date || a.created_at || 0);
      const bDate = new Date(b.analysis_date || b.created_at || 0);
      return bDate - aDate; // Most recent first
    })[0];
  }, [properties]);

  if (isLoading) {
    return (
      <div style={{
        backgroundColor: theme.cardBg,
        borderRadius: '16px',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
        border: `1px solid ${theme.border}`,
        padding: '2rem',
        transition: 'all 0.3s ease'
      }}>
        <div style={{
          padding: '1.5rem',
          borderBottom: `1px solid ${theme.border}`,
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem'
        }}>
          <BarChart3 size={20} style={{ color: currentPalette.primary }} />
          <div>
            <h3 style={{
              fontSize: '1.125rem',
              fontWeight: '600',
              color: theme.text,
              margin: 0
            }}>
              Last Property Analyzed
            </h3>
            <p style={{
              fontSize: '0.875rem',
              color: theme.textSecondary,
              margin: '0.25rem 0 0 0'
            }}>
              View your most recent analysis results
            </p>
          </div>
        </div>
        <div style={{ padding: '2rem', textAlign: 'center' }}>
          <div className="spinner" style={{ width: '32px', height: '32px', margin: '0 auto 1rem' }}></div>
          <p style={{ color: theme.textSecondary }}>Loading last property...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        backgroundColor: theme.cardBg,
        borderRadius: '16px',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
        border: `1px solid ${theme.border}`,
        padding: '2rem',
        transition: 'all 0.3s ease'
      }}>
        <div style={{
          padding: '1.5rem',
          borderBottom: `1px solid ${theme.border}`,
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem'
        }}>
          <BarChart3 size={20} style={{ color: currentPalette.primary }} />
          <div>
            <h3 style={{
              fontSize: '1.125rem',
              fontWeight: '600',
              color: theme.text,
              margin: 0
            }}>
              Last Property Analyzed
            </h3>
            <p style={{
              fontSize: '0.875rem',
              color: theme.textSecondary,
              margin: '0.25rem 0 0 0'
            }}>
              No properties analyzed yet
            </p>
          </div>
        </div>
        <div style={{ padding: '2rem', textAlign: 'center' }}>
          <p style={{ color: theme.textSecondary, fontSize: '0.875rem', margin: 0 }}>
            Analyze your first property above to see a summary here.
          </p>
        </div>
      </div>
    );
  }

  if (!lastProperty) {
    return (
      <div style={{
        backgroundColor: theme.cardBg,
        borderRadius: '16px',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
        border: `1px solid ${theme.border}`,
        padding: '2rem',
        transition: 'all 0.3s ease'
      }}>
        <div style={{
          padding: '1.5rem',
          borderBottom: `1px solid ${theme.border}`,
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem'
        }}>
          <BarChart3 size={20} style={{ color: currentPalette.primary }} />
          <h3 style={{
            fontSize: '1.125rem',
            fontWeight: '600',
            color: theme.text,
            margin: 0
          }}>
            Last Property Analyzed
          </h3>
        </div>
        <div style={{ padding: '2rem', textAlign: 'center' }}>
          <p style={{ color: theme.textSecondary }}>Error loading property data</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      backgroundColor: theme.cardBg,
      borderRadius: '16px',
      boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
      border: `1px solid ${theme.border}`,
      transition: 'all 0.3s ease'
    }}>
      {/* Update Results Section */}
      {/* <UpdateResultsSection 
        lastUpdateSummary={lastUpdateSummary}
        isExpanded={showUpdateResults}
        setIsExpanded={setShowUpdateResults}
      /> */}

      {/* Last Property Summary */}
      <div>
        <div style={{
          padding: '1.5rem',
          borderBottom: `1px solid ${theme.border}`,
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem'
        }}>
          <BarChart3 size={20} style={{ color: currentPalette.primary }} />
          <div>
            <h3 style={{
              fontSize: '1.125rem',
              fontWeight: '600',
              color: theme.text,
              margin: 0
            }}>
              Last Property Analyzed
            </h3>
            <p style={{
              fontSize: '0.875rem',
              color: theme.textSecondary,
              margin: '0.25rem 0 0 0'
            }}>
              View your most recent analysis results
            </p>
          </div>
        </div>
        
        {/* Property Summary Table */}
        <div style={{ overflow: 'auto' }}>
          <table style={{ 
            width: '100%', 
            borderCollapse: 'collapse',
            fontSize: '0.875rem'
          }}>
            <thead>
              <tr style={{ 
                backgroundColor: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : '#f8fafc', 
                borderBottom: `2px solid ${theme.border}`
              }}>
                <th style={{ padding: '0.75rem', textAlign: 'left', color: theme.text }}>Available Rooms</th>
                <th style={{ padding: '0.75rem', color: theme.text }}>Annual Income</th>
                <th style={{ padding: '0.75rem', color: theme.text }}>Status</th>
                <th style={{ padding: '0.75rem', color: theme.text }}>Advertiser</th>
                <th style={{ padding: '0.75rem', color: theme.text }}>Date Found</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ padding: '0.75rem', verticalAlign: 'top' }}>
                  {formatAvailableRooms(
                    lastProperty.available_rooms_details, 
                    lastProperty.available_rooms, 
                    lastProperty
                  )}
                </td>
                
                <td style={{ padding: '0.75rem' }}>
                  <div style={{ fontWeight: '500', color: theme.text }}>
                    {formatCurrency(lastProperty.annual_income)}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: theme.textSecondary }}>
                    per year
                  </div>
                </td>
                
                <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                  <div style={{ 
                    fontWeight: '500',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    display: 'inline-block',
                    fontSize: '0.75rem',
                    backgroundColor: getStatusColor(lastProperty.listing_status).bg,
                    color: getStatusColor(lastProperty.listing_status).color,
                    marginBottom: '4px'
                  }}>
                    {lastProperty.listing_status || 'N/A'}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: theme.textSecondary }}>
                    {lastProperty.bills_included === 'yes' ? '✅ Bills Inc.' : 
                    lastProperty.bills_included === 'no' ? '❌ Bills Not Inc.' : ''}
                  </div>
                </td>
                
                <td style={{ padding: '0.75rem' }}>
                  <div style={{ fontWeight: '500', color: theme.text }}>
                    {lastProperty.advertiser_name || 'N/A'}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: theme.textSecondary }}>
                    {lastProperty.landlord_type || 'Type unknown'}
                  </div>
                </td>
                
                <td style={{ padding: '0.75rem' }}>
                  <div style={{ color: theme.text }}>
                    {formatDate(lastProperty.date_found || lastProperty.analysis_date || lastProperty.created_at)}
                  </div>
                  {lastProperty.has_updates && (
                    <div style={{ fontSize: '0.7rem', color: '#059669', fontWeight: '500', marginTop: '2px' }}>
                      🔄 Has updates
                    </div>
                  )}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Quick Actions */}
        <div style={{ 
          display: 'flex', 
          gap: '1rem', 
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '1.5rem',
          borderTop: `1px solid ${theme.border}`,
          flexWrap: 'wrap'
        }}>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <Link 
              to={`/property/${lastProperty.property_id}`}
              style={{
                backgroundColor: currentPalette.primary,
                color: 'white',
                padding: '0.5rem 1rem',
                border: 'none',
                borderRadius: '6px',
                fontSize: '0.875rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                textDecoration: 'none',
                transition: 'all 0.2s ease'
              }}
            >
              <FileText size={16} />
              Full Details
            </Link>

            {lastProperty.url && (
              <a
                href={lastProperty.url}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  backgroundColor: 'transparent',
                  color: theme.textSecondary,
                  padding: '0.5rem 1rem',
                  border: `1px solid ${theme.border}`,
                  borderRadius: '6px',
                  fontSize: '0.875rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  textDecoration: 'none',
                  transition: 'all 0.2s ease'
                }}
              >
                <ExternalLink size={16} />
                Original Listing
              </a>
            )}
          </div>

          <Link 
            to="/history"
            style={{ 
              fontSize: '0.875rem',
              color: currentPalette.primary,
              textDecoration: 'none',
              fontWeight: '500'
            }}
          >
            View All Properties →
          </Link>
        </div>
      </div>
    </div>
  );
};

export default LastPropertySummary;