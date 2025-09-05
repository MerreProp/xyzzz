// Replace your TodaySection.jsx with this React Query version:

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { useDarkMode } from '../contexts/DarkModeContext';
import { useQuery } from '@tanstack/react-query';

const TodaySection = () => {
  const { currentPalette } = useTheme();
  const { isDarkMode } = useDarkMode();
  const navigate = useNavigate();

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

  // 🔧 CONVERT TO REACT QUERY: This will auto-refresh when cache is invalidated
  const { 
    data: todayProperties = [], 
    isLoading: loading, 
    error,
    refetch: fetchTodayProperties
  } = useQuery({
    queryKey: ['properties-today'],
    queryFn: async () => {
      const response = await fetch('/api/properties/today');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data.properties || [];
    },
    staleTime: 1000 * 30, // Fresh for 30 seconds
    refetchOnWindowFocus: false,
  });

  // Reuse the same formatting functions from History.jsx
  const formatCurrency = (value) => {
    if (!value || value === 0) return '—';
    return `£${value.toLocaleString()}`;
  };

  const formatAvailableRooms = (roomsDetails, roomsCount, property) => {
    if (!roomsDetails || roomsDetails.length === 0) {
      return roomsCount ? `${roomsCount} room${roomsCount !== 1 ? 's' : ''}` : '—';
    }

    return (
      <div>
        <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>
          {roomsCount || roomsDetails.length} available
        </div>
        <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
          {roomsDetails.slice(0, 2).map((room, idx) => (
            <div key={idx}>{room}</div>
          ))}
          {roomsDetails.length > 2 && (
            <div style={{ fontStyle: 'italic' }}>
              +{roomsDetails.length - 2} more...
            </div>
          )}
        </div>
      </div>
    );
  };

  const getDateGoneDisplay = (dateGone) => {
    if (!dateGone) return '—';
    
    try {
      const date = new Date(dateGone);
      const now = new Date();
      const daysDiff = Math.floor((now - date) / (1000 * 60 * 60 * 24));
      
      const formattedDate = date.toLocaleDateString('en-GB', {
        day: '2-digit',
        month: '2-digit',
        year: '2-digit'
      });
      
      if (daysDiff <= 30) {
        return (
          <div>
            <div style={{ fontSize: '0.875rem' }}>{formattedDate}</div>
            <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
              {daysDiff === 0 ? 'Today' : 
               daysDiff === 1 ? 'Yesterday' : 
               `${daysDiff} days ago`}
            </div>
          </div>
        );
      }
      
      return formattedDate;
    } catch (error) {
      return '—';
    }
  };

  const handleRowClick = (propertyId) => {
    navigate(`/property/${propertyId}`);
  };

  if (loading) {
    return (
      <div style={{ 
        marginBottom: '2rem',
        padding: '2rem',
        backgroundColor: '#f8fafc',
        borderRadius: '12px',
        border: '1px solid #e2e8f0',
        textAlign: 'center'
      }}>
        <div style={{ fontSize: '1rem', color: '#64748b' }}>
          Loading today's properties...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ 
        marginBottom: '2rem',
        padding: '2rem',
        backgroundColor: '#fef2f2',
        borderRadius: '12px',
        border: '1px solid #fecaca',
        textAlign: 'center'
      }}>
        <div style={{ fontSize: '1rem', color: '#dc2626', marginBottom: '0.5rem' }}>
          ⚠️ Error Loading Today's Properties
        </div>
        <div style={{ fontSize: '0.875rem', color: '#7f1d1d', marginBottom: '1rem' }}>
          {error.message}
        </div>
        <button 
          onClick={() => fetchTodayProperties()}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: '#dc2626',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '0.875rem'
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  if (todayProperties.length === 0) {
    return (
      <div style={{ 
        marginBottom: '2rem',
        padding: '2rem',
        backgroundColor: '#f0fdf4',
        borderRadius: '12px',
        border: '1px solid #bbf7d0',
        textAlign: 'center'
      }}>
        <div style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>✨</div>
        <div style={{ fontSize: '1rem', color: '#15803d', fontWeight: '600', marginBottom: '0.25rem' }}>
          No Properties Added Today
        </div>
        <div style={{ fontSize: '0.875rem', color: '#166534' }}>
          Properties you analyze today will appear here
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
      padding: '2rem',
      transition: 'all 0.3s ease',
      marginTop: '0'
    }}>
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: '0.75rem',
        marginBottom: '1rem',
        padding: '0.75rem 1rem',
        backgroundColor: '#fefce8',
        borderRadius: '8px',
        border: '1px solid #fbbf24'
      }}>
        <span style={{ fontSize: '1.5rem' }}>📅</span>
        <div>
          <h3 style={{ 
            margin: 0, 
            fontSize: '1.125rem', 
            fontWeight: '600',
            color: '#92400e'
          }}>
            Properties Added Today
          </h3>
          <p style={{ 
            margin: 0, 
            fontSize: '0.875rem', 
            color: '#78350f'
          }}>
            {todayProperties.length} propert{todayProperties.length !== 1 ? 'ies' : 'y'} analyzed today
          </p>
        </div>
      </div>

      {/* Table - Same structure as main History table */}
      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th>Property</th>
              <th>Available Rooms</th>
              <th>Monthly Income</th>
              <th>Total Rooms</th>
              <th>Status</th>
              <th>Advertiser</th>
              <th>Date Found</th>
              <th>Date Gone</th>
            </tr>
          </thead>
          <tbody>
            {todayProperties.map((property) => (
              <tr 
                key={property.property_id}
                onClick={() => handleRowClick(property.property_id)}
                style={{ 
                  cursor: 'pointer',
                  backgroundColor: '#fffbeb',
                  borderLeft: '3px solid #f59e0b'
                }}
                className="clickable-row"
              >
                <td>
                  <div>
                    <div style={{ fontWeight: '500', marginBottom: '0.25rem' }}>
                      {property.address || 'Address not available'}
                    </div>
                    {property.has_updates && (
                      <div style={{ 
                        fontSize: '0.75rem', 
                        color: '#059669',
                        fontWeight: '500',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.25rem'
                      }}>
                        🔄 Updated ({property.total_analyses} analyses)
                      </div>
                    )}
                  </div>
                </td>

                <td>
                  {formatAvailableRooms(property.available_rooms_details, property.available_rooms, property)}
                </td>
                
                <td>
                  <div style={{ fontWeight: '600' }}>
                    {formatCurrency(property.monthly_income)}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                    {formatCurrency(property.annual_income)} / year
                  </div>
                </td>

                <td>
                  <div style={{ 
                    fontSize: '1.125rem', 
                    fontWeight: '600',
                    textAlign: 'center'
                  }}>
                    {property.total_rooms || '—'}
                  </div>
                </td>

                <td>
                  <div style={{ fontSize: '0.875rem' }}>
                    {property.meets_requirements && (
                      <div style={{ 
                        color: property.meets_requirements.toLowerCase().includes('yes') ? '#059669' : '#dc2626',
                        fontWeight: '500',
                        marginBottom: '0.25rem'
                      }}>
                        {property.meets_requirements.toLowerCase().includes('yes') ? '✅ Viable' : '❌ Not Viable'}
                      </div>
                    )}
                    {property.bills_included && (
                      <div style={{ color: '#64748b', fontSize: '0.75rem' }}>
                        Bills: {property.bills_included}
                      </div>
                    )}
                  </div>
                </td>

                <td>
                  <div style={{ fontSize: '0.875rem', maxWidth: '150px' }}>
                    <div style={{ fontWeight: '500', marginBottom: '0.25rem' }}>
                      {property.advertiser_name || '—'}
                    </div>
                    {property.landlord_type && (
                      <div style={{ color: '#64748b', fontSize: '0.75rem' }}>
                        {property.landlord_type}
                      </div>
                    )}
                  </div>
                </td>

                <td>
                  <div style={{ fontSize: '0.875rem', textAlign: 'center', fontWeight: '600', color: '#059669' }}>
                    {property.date_found || 'Today'}
                  </div>
                </td>

                <td>
                  <div style={{ fontSize: '0.875rem', textAlign: 'center' }}>
                    {getDateGoneDisplay(property.date_gone)}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TodaySection;