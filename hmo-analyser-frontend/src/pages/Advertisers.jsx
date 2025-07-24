// Updated Advertisers.jsx - Overview page with Phase 1 Date Gone functionality

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import { propertyApi } from '../utils/api';

const Advertisers = () => {
  const navigate = useNavigate();
  const [sortBy, setSortBy] = useState('listing_count');
  const [sortOrder, setSortOrder] = useState('desc');

  // Fetch all properties
  const { data: properties = [], isLoading, error } = useQuery({
    queryKey: ['properties'],
    queryFn: propertyApi.getAllProperties,
  });

  // PHASE 1: Enhanced statistics function with date gone tracking
  const getAdvertiserStatsWithDateGone = (properties) => {
    const totalProperties = properties.length;
    const totalIncome = properties.reduce((sum, prop) => 
      sum + (Number(prop.monthly_income) || 0), 0
    );
    const viableProperties = properties.filter(prop => 
      prop.meets_requirements?.toLowerCase().includes('yes')
    ).length;
    const propertiesGone = properties.filter(prop => 
      prop.date_gone
    ).length; // NEW - Phase 1 addition
    const avgRooms = properties.reduce((sum, prop) => 
      sum + (Number(prop.total_rooms) || 0), 0
    ) / totalProperties;
    const billsIncludedCount = properties.filter(prop => 
      prop.bills_included?.toLowerCase() === 'yes'
    ).length;
    
    return {
      totalProperties,
      totalIncome,
      viableProperties,
      propertiesGone, // NEW - Phase 1 addition
      avgRooms: Math.round(avgRooms * 10) / 10,
      viabilityRate: Math.round((viableProperties / totalProperties) * 100),
      billsIncludedCount
    };
  };

  // Group properties by advertiser with enhanced stats
  const advertiserData = React.useMemo(() => {
    const grouped = {};
    
    properties.forEach(property => {
      const advertiserName = property.advertiser_name || 'Unknown Advertiser';
      
      if (!grouped[advertiserName]) {
        grouped[advertiserName] = {
          name: advertiserName,
          properties: [],
          mostRecentDate: null
        };
      }
      
      grouped[advertiserName].properties.push(property);

      // Track most recent analysis date
      if (property.analysis_date) {
        const propDate = new Date(property.analysis_date);
        if (!grouped[advertiserName].mostRecentDate || propDate > grouped[advertiserName].mostRecentDate) {
          grouped[advertiserName].mostRecentDate = propDate;
        }
      }
    });

    // Calculate enhanced statistics for each advertiser
    Object.values(grouped).forEach(advertiser => {
      const stats = getAdvertiserStatsWithDateGone(advertiser.properties);
      Object.assign(advertiser, stats);
    });

    return grouped;
  }, [properties]);

  // Get list of advertisers for sorting
  const advertisersList = Object.values(advertiserData);

  // Sort advertisers
  const sortedAdvertisers = [...advertisersList].sort((a, b) => {
    let aValue, bValue;
    
    switch (sortBy) {
      case 'listing_count':
        aValue = a.totalProperties;
        bValue = b.totalProperties;
        break;
      case 'total_income':
        aValue = a.totalIncome;
        bValue = b.totalIncome;
        break;
      case 'viability_rate':
        aValue = a.viabilityRate;
        bValue = b.viabilityRate;
        break;
      case 'avg_rooms':
        aValue = a.avgRooms;
        bValue = b.avgRooms;
        break;
      case 'properties_gone': // NEW - Phase 1 addition
        aValue = a.propertiesGone;
        bValue = b.propertiesGone;
        break;
      case 'name':
        aValue = a.name.toLowerCase();
        bValue = b.name.toLowerCase();
        break;
      default:
        aValue = a.totalProperties;
        bValue = b.totalProperties;
    }

    if (sortBy === 'name') {
      return sortOrder === 'asc' ? (aValue > bValue ? 1 : -1) : (aValue < bValue ? 1 : -1);
    } else {
      aValue = Number(aValue) || 0;
      bValue = Number(bValue) || 0;
      return sortOrder === 'asc' ? (aValue - bValue) : (bValue - aValue);
    }
  });

  const formatCurrency = (amount) => {
    if (!amount) return 'N/A';
    return `£${Number(amount).toLocaleString()}`;
  };

  const handleAdvertiserClick = (advertiserName) => {
    navigate(`/advertiser/${encodeURIComponent(advertiserName)}`);
  };

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem' }}>
        <div className="spinner" style={{ width: '40px', height: '40px', margin: '0 auto 1rem' }}></div>
        <p>Loading advertisers data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <h2 className="card-title">❌ Error Loading Advertisers</h2>
        <p style={{ color: '#dc2626', marginBottom: '1rem' }}>
          Failed to load advertisers data. Please check your connection.
        </p>
        <Link to="/history" className="btn btn-primary">
          ← Back to History
        </Link>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
          <div>
            <h1 style={{ fontSize: '2rem', fontWeight: 'bold', color: '#1e293b', marginBottom: '0.5rem' }}>
              Advertisers Overview
            </h1>
            <p style={{ color: '#64748b', fontSize: '1.1rem' }}>
              Browse all advertisers and their property portfolios
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

      {/* Summary Stats - Enhanced with Phase 1 data */}
      <div className="results-grid" style={{ marginBottom: '2rem' }}>
        <div className="metric-card">
          <div className="metric-value">{advertisersList.length}</div>
          <div className="metric-label">Total Advertisers</div>
        </div>
        
        <div className="metric-card">
          <div className="metric-value">{properties.length}</div>
          <div className="metric-label">Total Listings</div>
        </div>
        
        <div className="metric-card">
          <div className="metric-value">
            {Math.round((properties.length / advertisersList.length) * 10) / 10 || 0}
          </div>
          <div className="metric-label">Avg Properties per Advertiser</div>
        </div>
        
        <div className="metric-card">
          <div className="metric-value">
            {sortedAdvertisers[0]?.totalProperties || 0}
          </div>
          <div className="metric-label">Most Active Advertiser</div>
        </div>

        {/* NEW - Phase 1 addition */}
        <div className="metric-card" style={{ borderLeftColor: '#dc2626' }}>
          <div className="metric-value" style={{ color: '#dc2626' }}>
            {properties.filter(p => p.date_gone).length}
          </div>
          <div className="metric-label">Properties Currently Gone</div>
        </div>

        <div className="metric-card" style={{ borderLeftColor: '#059669' }}>
          <div className="metric-value" style={{ color: '#059669' }}>
            {properties.filter(p => !p.date_gone).length}
          </div>
          <div className="metric-label">Properties Available</div>
        </div>
      </div>

      {/* Sort Controls - Enhanced with Phase 1 options */}
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
              <option value="listing_count">Number of Properties</option>
              <option value="total_income">Total Income</option>
              <option value="viability_rate">Viability Rate</option>
              <option value="avg_rooms">Average Rooms</option>
              <option value="properties_gone">Properties Gone</option>
              <option value="name">Name</option>
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
            Click on any advertiser to view their properties
          </div>
        </div>
      </div>

      {/* Advertisers Grid - Enhanced with Phase 1 data */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '1.5rem' }}>
        {sortedAdvertisers.map((advertiser, index) => (
          <div 
            key={advertiser.name}
            style={{ 
              padding: '1.5rem',
              border: '1px solid #e2e8f0',
              borderRadius: '12px',
              backgroundColor: 'white',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
            }}
            onClick={() => handleAdvertiserClick(advertiser.name)}
            onMouseEnter={(e) => {
              e.target.style.transform = 'translateY(-2px)';
              e.target.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = '0 1px 3px rgba(0, 0, 0, 0.1)';
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
              <div>
                <h3 style={{ fontWeight: '600', color: '#1e293b', marginBottom: '0.25rem', fontSize: '1.1rem' }}>
                  {advertiser.name}
                </h3>
                <div style={{ fontSize: '0.875rem', color: '#64748b' }}>
                  {advertiser.totalProperties} {advertiser.totalProperties === 1 ? 'property' : 'properties'}
                  {/* NEW - Phase 1 addition: Show gone properties if any */}
                  {advertiser.propertiesGone > 0 && (
                    <span style={{ color: '#dc2626', marginLeft: '0.5rem' }}>
                      ({advertiser.propertiesGone} gone)
                    </span>
                  )}
                </div>
              </div>
              {index < 3 && (
                <div style={{ fontSize: '1.5rem' }}>
                  {index === 0 ? '🥇' : index === 1 ? '🥈' : '🥉'}
                </div>
              )}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
              <div>
                <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '2px' }}>Monthly Income</div>
                <div style={{ fontWeight: '600', color: '#059669' }}>{formatCurrency(advertiser.totalIncome)}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '2px' }}>Viability Rate</div>
                <div style={{ fontWeight: '600' }}>{advertiser.viabilityRate}%</div>
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '2px' }}>Avg Rooms</div>
                <div style={{ fontWeight: '600' }}>{advertiser.avgRooms}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '2px' }}>Bills Included</div>
                <div style={{ fontWeight: '600' }}>{advertiser.billsIncludedCount}</div>
              </div>
              
              {/* NEW - Phase 1 addition: Properties Gone stat */}
              <div>
                <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '2px' }}>Properties Gone</div>
                <div style={{ 
                  fontWeight: '600', 
                  color: advertiser.propertiesGone > 0 ? '#dc2626' : '#64748b'
                }}>
                  {advertiser.propertiesGone}
                </div>
              </div>
              
              <div>
                <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '2px' }}>Properties Active</div>
                <div style={{ fontWeight: '600', color: '#059669' }}>
                  {advertiser.totalProperties - advertiser.propertiesGone}
                </div>
              </div>
            </div>

            {/* Status indicator for advertisers with gone properties */}
            {advertiser.propertiesGone > 0 && (
              <div style={{ 
                padding: '0.5rem', 
                backgroundColor: '#fee2e2', 
                borderRadius: '6px',
                marginBottom: '0.75rem',
                fontSize: '0.75rem',
                color: '#991b1b',
                textAlign: 'center'
              }}>
                ⚠️ {advertiser.propertiesGone} {advertiser.propertiesGone === 1 ? 'property is' : 'properties are'} currently offline
              </div>
            )}

            <div style={{ 
              padding: '0.75rem', 
              backgroundColor: '#f8fafc', 
              borderRadius: '6px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '0.875rem', color: '#667eea', fontWeight: '500' }}>
                Click to view all properties →
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Footer Info - Enhanced with Phase 1 information */}
      <div style={{ 
        marginTop: '2rem', 
        padding: '1rem', 
        backgroundColor: '#f8fafc', 
        borderRadius: '8px',
        fontSize: '0.875rem',
        color: '#64748b'
      }}>
        💡 <strong>Tip:</strong> Click on any advertiser card to view all their property listings. Each advertiser page shows detailed analytics and property comparisons. Properties marked as "gone" have no currently available rooms.
      </div>
    </div>
  );
};

export default Advertisers;