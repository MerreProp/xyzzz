// LastPropertySummary.jsx - Shows summary of the most recent analyzed property

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { propertyApi } from '../utils/api';

const LastPropertySummary = () => {
  // Fetch all properties to get the most recent one
  const { data: properties = [], isLoading, error } = useQuery({
    queryKey: ['properties-last'],
    queryFn: propertyApi.getAllProperties,
  });

  // Helper functions (same as History.jsx)
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
        room => room.current_status === 'available' && room.is_currently_listed
      );
      
      if (availableRoomsWithHistory.length > 0) {
        return (
          <div style={{ lineHeight: '1.4' }}>
            {availableRoomsWithHistory.map((room, index) => (
              <div key={index} style={{ fontSize: '0.875rem', marginBottom: '2px' }}>
                {index + 1} - {room.price_text} {room.room_type && `(${room.room_type})`}
              </div>
            ))}
          </div>
        );
      }
    }

    // Fallback to legacy availableRoomsDetails
    if (availableRoomsDetails && Array.isArray(availableRoomsDetails) && availableRoomsDetails.length > 0) {
      return (
        <div style={{ lineHeight: '1.4' }}>
          {availableRoomsDetails.map((room, index) => (
            <div key={index} style={{ fontSize: '0.875rem', marginBottom: '2px' }}>
              {room}
            </div>
          ))}
        </div>
      );
    }

    if (availableRooms && availableRooms > 0) {
      return (
        <div style={{ fontSize: '0.875rem', color: '#059669', fontWeight: '500' }}>
          {availableRooms} available
        </div>
      );
    }

    return (
      <span style={{ color: '#64748b', fontSize: '0.875rem' }}>
        No rooms available
      </span>
    );
  };

  const getStatusColor = (status) => {
    if (!status) return { bg: '#f1f5f9' };
    
    const statusLower = status.toLowerCase();
    
    if (statusLower.includes('boosted')) {
      return { bg: '#dbeafe' };
    } else if (statusLower.includes('new today')) {
      return { bg: '#dcfce7' };
    } else if (statusLower === 'new') {
      return { bg: '#fed7aa' };
    } else if (statusLower.includes('featured')) {
      return { bg: '#fef3c7' };
    } else {
      return { bg: '#f1f5f9' };
    }
  };

  const getViabilityBadge = (meets) => {
    if (!meets) return <span className="status-badge">Unknown</span>;
    
    if (meets.toLowerCase().includes('yes')) {
      return <span className="status-badge success">✅ Viable</span>;
    } else {
      return <span className="status-badge error">❌ Issues</span>;
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
      <div className="card" style={{ marginBottom: '2rem' }}>
        <div className="card-header">
          <h3 className="card-title">📊 Last Property Analyzed</h3>
        </div>
        <div style={{ padding: '2rem', textAlign: 'center' }}>
          <div className="spinner" style={{ width: '32px', height: '32px', margin: '0 auto 1rem' }}></div>
          <p style={{ color: '#64748b' }}>Loading last property...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card" style={{ marginBottom: '2rem' }}>
        <div className="card-header">
          <h3 className="card-title">📊 Last Property Analyzed</h3>
        </div>
        <div style={{ padding: '2rem', textAlign: 'center' }}>
          <p style={{ color: '#dc2626' }}>Error loading property data</p>
        </div>
      </div>
    );
  }

  if (!lastProperty) {
    return (
      <div className="card" style={{ marginBottom: '2rem' }}>
        <div className="card-header">
          <h3 className="card-title">📊 Last Property Analyzed</h3>
        </div>
        <div style={{ padding: '2rem', textAlign: 'center' }}>
          <p style={{ color: '#64748b', marginBottom: '1rem' }}>
            No properties analyzed yet.
          </p>
          <p style={{ color: '#64748b', fontSize: '0.875rem' }}>
            Analyze your first property above to see a summary here.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="card" style={{ marginBottom: '2rem' }}>
      <div className="card-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h3 className="card-title">📊 Last Property Analyzed</h3>
            <p className="card-subtitle" style={{ marginTop: '0.25rem' }}>
              Most recent analysis • {formatDate(lastProperty.analysis_date || lastProperty.created_at)}
            </p>
          </div>
          <Link 
            to={`/property/${lastProperty.property_id}`}
            className="btn btn-secondary"
            style={{ 
              fontSize: '0.875rem',
              padding: '0.5rem 1rem'
            }}
          >
            View Details →
          </Link>
        </div>
      </div>

      {/* Property Overview */}
      <div style={{ 
        padding: '1.5rem',
        backgroundColor: '#f8fafc',
        border: '1px solid #e2e8f0',
        borderRadius: '8px',
        marginBottom: '1.5rem'
      }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          {/* Address */}
          <div>
            <div style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '0.25rem' }}>
              📍 Address
            </div>
            <div style={{ fontWeight: '500', fontSize: '0.95rem' }}>
              {lastProperty.address || 'Address not available'}
            </div>
          </div>

          {/* Viability */}
          <div>
            <div style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '0.25rem' }}>
              ✅ Viability
            </div>
            <div>
              {getViabilityBadge(lastProperty.meets_requirements)}
            </div>
          </div>

          {/* Monthly Income */}
          <div>
            <div style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '0.25rem' }}>
              💰 Monthly Income
            </div>
            <div style={{ fontWeight: '600', fontSize: '1.1rem', color: '#059669' }}>
              {formatCurrency(lastProperty.monthly_income)}
            </div>
          </div>

          {/* Total Rooms */}
          <div>
            <div style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '0.25rem' }}>
              🏠 Total Rooms
            </div>
            <div style={{ fontWeight: '500', fontSize: '1.1rem' }}>
              {lastProperty.total_rooms || 'N/A'}
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Information Table */}
      <div className="table-container" style={{ overflowX: 'auto' }}>
        <table className="table" style={{ fontSize: '0.875rem' }}>
          <thead>
            <tr style={{ backgroundColor: '#f8fafc' }}>
              <th style={{ padding: '0.75rem' }}>Available Rooms</th>
              <th style={{ padding: '0.75rem' }}>Annual Income</th>
              <th style={{ padding: '0.75rem' }}>Status</th>
              <th style={{ padding: '0.75rem' }}>Advertiser</th>
              <th style={{ padding: '0.75rem' }}>Date Found</th>
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
                <div style={{ fontWeight: '500' }}>
                  {formatCurrency(lastProperty.annual_income)}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
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
                  marginBottom: '4px'
                }}>
                  {lastProperty.listing_status || 'N/A'}
                </div>
                <div style={{ fontSize: '0.7rem', color: '#64748b' }}>
                  {lastProperty.bills_included === 'yes' ? '✅ Bills Inc.' : 
                  lastProperty.bills_included === 'no' ? '❌ Bills Not Inc.' : ''}
                </div>
              </td>
              
              <td style={{ padding: '0.75rem' }}>
                <div style={{ fontWeight: '500' }}>
                  {lastProperty.advertiser_name || 'N/A'}
                </div>
                <div style={{ fontSize: '0.7rem', color: '#64748b' }}>
                  {lastProperty.landlord_type || 'Type unknown'}
                </div>
              </td>
              
              <td style={{ padding: '0.75rem' }}>
                <div>
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
        paddingTop: '1rem',
        borderTop: '1px solid #e2e8f0',
        flexWrap: 'wrap'
      }}>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <Link 
            to={`/property/${lastProperty.property_id}`}
            className="btn btn-primary"
            style={{ fontSize: '0.875rem' }}
          >
            📋 Full Details
          </Link>
          
          {lastProperty.url && (
            <a
              href={lastProperty.url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-secondary"
              style={{ fontSize: '0.875rem' }}
            >
              🔗 Original Listing
            </a>
          )}
        </div>

        <Link 
          to="/history"
          style={{ 
            fontSize: '0.875rem',
            color: '#6366f1',
            textDecoration: 'none',
            fontWeight: '500'
          }}
        >
          View All Properties →
        </Link>
      </div>
    </div>
  );
};

export default LastPropertySummary;