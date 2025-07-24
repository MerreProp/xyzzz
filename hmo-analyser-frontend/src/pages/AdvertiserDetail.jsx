import React, { useState, useMemo } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { propertyApi } from '../utils/api';

const AdvertiserDetail = () => {
  const { advertiserName } = useParams();
  const navigate = useNavigate();
  
  // Decode the advertiser name from URL
  const decodedAdvertiserName = decodeURIComponent(advertiserName);
  
  const [sortBy, setSortBy] = useState('analysis_date');
  const [sortOrder, setSortOrder] = useState('desc');

  // Helper functions
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString('en-GB', {
        day: '2-digit',
        month: '2-digit',
        year: '2-digit'
      });
    } catch (error) {
      return 'Invalid Date';
    }
  };

  const formatDateTime = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleString('en-GB', {
        day: '2-digit',
        month: '2-digit',
        year: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (error) {
      return 'Invalid Date';
    }
  };

  const handleRowClick = (propertyId) => {
    navigate(`/property/${propertyId}`);
  };

  const formatAvailableRooms = (availableRoomsDetails) => {
    if (!availableRoomsDetails || availableRoomsDetails.length === 0) {
      return <span style={{ color: '#64748b', fontSize: '0.875rem' }}>No rooms available</span>;
    }

    return (
      <div style={{ lineHeight: '1.4' }}>
        {availableRoomsDetails.map((room, index) => (
          <div key={index} style={{ fontSize: '0.875rem', marginBottom: '2px' }}>
            {room}
          </div>
        ))}
      </div>
    );
  };

  // Fetch all properties
  const { data: allProperties = [], isLoading, error } = useQuery({
    queryKey: ['properties'],
    queryFn: propertyApi.getAllProperties,
  });

  // Filter properties for this advertiser
  const advertiserProperties = useMemo(() => {
    return allProperties.filter(property => 
      property.advertiser_name === decodedAdvertiserName
    );
  }, [allProperties, decodedAdvertiserName]);

  // Calculate advertiser stats
  const advertiserStats = useMemo(() => {
    if (advertiserProperties.length === 0) return null;

    const totalProperties = advertiserProperties.length;
    const totalIncome = advertiserProperties.reduce((sum, prop) => 
      sum + (Number(prop.monthly_income) || 0), 0
    );
    const viableProperties = advertiserProperties.filter(prop => 
      prop.meets_requirements?.toLowerCase().includes('yes')
    ).length;
    const avgRooms = advertiserProperties.reduce((sum, prop) => 
      sum + (Number(prop.total_rooms) || 0), 0
    ) / totalProperties;
    const billsIncludedCount = advertiserProperties.filter(prop => 
      prop.bills_included?.toLowerCase() === 'yes'
    ).length;

    return {
      totalProperties,
      totalIncome,
      viableProperties,
      avgRooms: Math.round(avgRooms * 10) / 10,
      billsIncludedCount,
      viabilityRate: Math.round((viableProperties / totalProperties) * 100)
    };
  }, [advertiserProperties]);

  // Sort properties
  const sortedProperties = useMemo(() => {
    return [...advertiserProperties].sort((a, b) => {
      let aValue = a[sortBy];
      let bValue = b[sortBy];

      if (sortBy === 'monthly_income' || sortBy === 'annual_income' || sortBy === 'total_rooms') {
        aValue = Number(aValue) || 0;
        bValue = Number(bValue) || 0;
      } else if (sortBy === 'analysis_date') {
        aValue = new Date(aValue || 0);
        bValue = new Date(bValue || 0);
      } else {
        aValue = String(aValue || '').toLowerCase();
        bValue = String(bValue || '').toLowerCase();
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });
  }, [advertiserProperties, sortBy, sortOrder]);

  const formatCurrency = (amount) => {
    if (!amount) return 'N/A';
    return `£${Number(amount).toLocaleString()}`;
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

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem' }}>
        <div className="spinner" style={{ width: '40px', height: '40px', margin: '0 auto 1rem' }}></div>
        <p>Loading advertiser data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <h2 className="card-title">❌ Error Loading Advertiser Data</h2>
        <p style={{ color: '#dc2626', marginBottom: '1rem' }}>
          Failed to load advertiser information. Please check your connection.
        </p>
        <Link to="/advertisers" className="btn btn-primary">
          ← Back to Advertisers
        </Link>
      </div>
    );
  }

  if (advertiserProperties.length === 0) {
    return (
      <div>
        {/* Header */}
        <div style={{ marginBottom: '2rem' }}>
          <Link 
            to="/advertisers" 
            style={{ 
              color: '#667eea', 
              textDecoration: 'none',
              fontSize: '0.875rem',
              marginBottom: '0.5rem',
              display: 'block'
            }}
          >
            ← Back to All Advertisers
          </Link>
          <h1 style={{ fontSize: '2rem', fontWeight: 'bold', color: '#1e293b', marginBottom: '0.5rem' }}>
            {decodedAdvertiserName}
          </h1>
        </div>

        <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
          <h3 style={{ color: '#64748b', marginBottom: '1rem' }}>No Properties Found</h3>
          <p style={{ color: '#64748b', marginBottom: '2rem' }}>
            No properties found for advertiser "{decodedAdvertiserName}".
          </p>
          <Link to="/advertisers" className="btn btn-primary">
            ← Back to All Advertisers
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
          <div>
            <Link 
              to="/advertisers" 
              style={{ 
                color: '#667eea', 
                textDecoration: 'none',
                fontSize: '0.875rem',
                marginBottom: '0.5rem',
                display: 'block'
              }}
            >
              ← Back to All Advertisers
            </Link>
            <h1 style={{ fontSize: '2rem', fontWeight: 'bold', color: '#1e293b', marginBottom: '0.5rem' }}>
              {decodedAdvertiserName}
            </h1>
            <p style={{ color: '#64748b', fontSize: '1.1rem' }}>
              All properties listed by this advertiser
            </p>
          </div>
          
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <Link to="/" className="btn btn-secondary">
              🔍 Analyze New Property
            </Link>
            <Link to="/history" className="btn btn-secondary">
              📋 View All Properties
            </Link>
          </div>
        </div>
      </div>

      {/* Advertiser Stats */}
      {advertiserStats && (
        <div className="results-grid" style={{ marginBottom: '2rem' }}>
          <div className="metric-card">
            <div className="metric-value">{advertiserStats.totalProperties}</div>
            <div className="metric-label">Total Properties</div>
          </div>
          
          <div className="metric-card">
            <div className="metric-value">{formatCurrency(advertiserStats.totalIncome)}</div>
            <div className="metric-label">Total Monthly Income</div>
          </div>
          
          <div className="metric-card">
            <div className="metric-value">{advertiserStats.viableProperties}</div>
            <div className="metric-label">Viable Properties</div>
          </div>
          
          <div className="metric-card">
            <div className="metric-value">{advertiserStats.viabilityRate}%</div>
            <div className="metric-label">Viability Rate</div>
          </div>

          <div className="metric-card">
            <div className="metric-value">{advertiserStats.avgRooms}</div>
            <div className="metric-label">Average Rooms</div>
          </div>

          <div className="metric-card">
            <div className="metric-value">{advertiserStats.billsIncludedCount}</div>
            <div className="metric-label">Bills Included Properties</div>
          </div>
        </div>
      )}

      {/* Sort Controls */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <div>
            <label style={{ fontSize: '0.875rem', color: '#64748b', marginRight: '0.5rem' }}>
              Sort by:
            </label>
            <select 
              value={sortBy} 
              onChange={(e) => setSortBy(e.target.value)}
              style={{ 
                padding: '0.5rem', 
                border: '1px solid #e5e7eb', 
                borderRadius: '6px',
                fontSize: '0.875rem'
              }}
            >
              <option value="analysis_date">Date Found</option>
              <option value="monthly_income">Monthly Income</option>
              <option value="annual_income">Annual Income</option>
              <option value="total_rooms">Total Rooms</option>
              <option value="address">Address</option>
              <option value="listing_status">Status</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.875rem', color: '#64748b', marginRight: '0.5rem' }}>
              Order:
            </label>
            <select 
              value={sortOrder} 
              onChange={(e) => setSortOrder(e.target.value)}
              style={{ 
                padding: '0.5rem', 
                border: '1px solid #e5e7eb', 
                borderRadius: '6px',
                fontSize: '0.875rem'
              }}
            >
              <option value="desc">Descending</option>
              <option value="asc">Ascending</option>
            </select>
          </div>

          <div style={{ marginLeft: 'auto', fontSize: '0.875rem', color: '#64748b' }}>
            Showing {sortedProperties.length} properties
          </div>
        </div>
      </div>

      {/* Properties Table */}
      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th>Property</th>
              <th>Available Rooms</th>
              <th>Monthly Income</th>
              <th>Total Rooms</th>
              <th>Status</th>
              <th>Date Found</th>
              <th>Date Gone</th>
            </tr>
          </thead>
          <tbody>
            {sortedProperties.map((property) => (
              <tr 
                key={property.property_id}
                onClick={() => handleRowClick(property.property_id)}
                className="clickable-row"
                style={{ cursor: 'pointer' }}
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
                  {formatAvailableRooms(property.available_rooms_details)}
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
                    fontWeight: '500',
                    fontSize: '1.5rem',
                    textAlign: 'center', 
                  }}>
                    {property.total_rooms || 'N/A'}
                  </div>
                </td>
                
                <td style={{ textAlign: 'center', verticalAlign: 'middle' }}>
                  <div style={{ 
                    fontWeight: '500',
                    padding: '6px 12px',
                    borderRadius: '6px',
                    display: 'inline-block',
                    fontSize: '0.875rem',
                    backgroundColor: getStatusColor(property.listing_status).bg,
                    color: '#000000',
                    textAlign: 'center',
                    minWidth: '80px'
                  }}>
                    {property.listing_status || 'N/A'}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '4px', textAlign: 'center' }}>
                    {property.bills_included === 'yes' ? '✅ Bills Inc.' : 
                     property.bills_included === 'no' ? '❌ Bills Not Inc.' : ''}
                  </div>
                </td>
                
                <td>
                  <div style={{ fontSize: '0.875rem' }}>
                    {formatDate(property.analysis_date)}
                  </div>
                  {property.last_updated && property.has_updates && (
                    <div style={{ fontSize: '0.75rem', color: '#059669', fontWeight: '500' }}>
                      Updated: {formatDateTime(property.last_updated)}
                    </div>
                  )}
                </td>

                <td>
                  <div style={{ fontSize: '0.875rem', color: '#64748b' }}>
                    {property.date_gone || '—'}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer Info */}
      <div style={{ 
        marginTop: '2rem', 
        padding: '1rem', 
        backgroundColor: '#f8fafc', 
        borderRadius: '8px',
        fontSize: '0.875rem',
        color: '#64748b'
      }}>
        💡 <strong>Tip:</strong> Click on any row to view detailed property information. This page shows all properties listed by {decodedAdvertiserName}.
      </div>
    </div>
  );
};

export default AdvertiserDetail;