import React from 'react';
import { propertyApi, downloadFile } from '../utils/api';

const ResultsCard = ({ property, taskId }) => {
  const handleExportExcel = async () => {
    try {
      const blob = await propertyApi.exportProperty(taskId);
      const filename = `hmo_analysis_${property['Property ID'] || taskId}.xlsx`;
      downloadFile(blob, filename);
    } catch (error) {
      console.error('Failed to export Excel:', error);
      alert('Failed to export Excel file. Please try again.');
    }
  };

  const formatCurrency = (amount) => {
    if (!amount) return 'N/A';
    return `£${amount.toLocaleString()}`;
  };

  const calculateDaysSinceFound = (analysisDateString) => {
    if (!analysisDateString) return 'N/A';
    
    try {
      // Parse the analysis date (format: dd/mm/yy)
      const parts = analysisDateString.split('/');
      if (parts.length !== 3) return 'N/A';
      
      const day = parseInt(parts[0], 10);
      const month = parseInt(parts[1], 10) - 1; // JavaScript months are 0-indexed
      let year = parseInt(parts[2], 10);
      
      // Handle 2-digit years (assume 20xx for years 00-99)
      if (year < 100) {
        year += 2000;
      }
      
      const analysisDate = new Date(year, month, day);
      const currentDate = new Date();
      
      // Calculate difference in days
      const timeDifference = currentDate - analysisDate;
      const daysDifference = Math.floor(timeDifference / (1000 * 60 * 60 * 24));
      
      return daysDifference >= 0 ? daysDifference : 'N/A';
    } catch (error) {
      console.error('Error calculating days since found:', error);
      return 'N/A';
    }
  };

  const getDaysColor = (days) => {
    if (days === 'N/A') return '#64748b';
    
    const numDays = parseInt(days, 10);
    if (numDays <= 7) return '#059669'; // Green for new (within a week)
    if (numDays <= 30) return '#f59e0b'; // Orange for recent (within a month)
    return '#dc2626'; // Red for old (over a month)
  };

  const getRequirementStatus = (meets) => {
    if (!meets) return { color: '#64748b', text: 'Unknown', bg: '#f1f5f9' };
    
    if (meets.toLowerCase().includes('yes')) {
      return { color: '#166534', text: 'Meets Requirements ✅', bg: '#dcfce7' };
    } else {
      return { color: '#991b1b', text: meets, bg: '#fee2e2' };
    }
  };

  const requirementStatus = getRequirementStatus(property['Meets Requirements']);
  const daysSinceFound = calculateDaysSinceFound(property['Analysis Date']);

  return (
    <div>
      {/* Header Section */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
          <div>
            <h2 className="card-title">🏠 Analysis Results</h2>
            <p className="card-subtitle">
              Property analysis completed on {property['Analysis Date']}
            </p>
          </div>
          <button 
            onClick={handleExportExcel}
            className="btn btn-secondary"
            title="Download Excel Report"
          >
            📄 Export Excel
          </button>
        </div>

        {/* Requirement Status Banner */}
        <div 
          style={{ 
            padding: '1rem', 
            borderRadius: '8px', 
            backgroundColor: requirementStatus.bg,
            color: requirementStatus.color,
            fontWeight: '600',
            marginBottom: '1.5rem'
          }}
        >
          {requirementStatus.text}
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="results-grid">
        <div className="metric-card">
          <div className="metric-value">
            {formatCurrency(property['Monthly Income'])}
          </div>
          <div className="metric-label">Monthly Income</div>
        </div>

        <div className="metric-card">
          <div className="metric-value">
            {formatCurrency(property['Annual Income'])}
          </div>
          <div className="metric-label">Annual Income</div>
        </div>

        <div className="metric-card">
          <div className="metric-value">
            {property['Total Rooms'] || 'N/A'}
          </div>
          <div className="metric-label">Total Rooms</div>
        </div>

        <div className="metric-card">
          <div className="metric-value">
            {property['Available Rooms'] !== null && property['Available Rooms'] !== undefined ? property['Available Rooms'] : 'N/A'}
          </div>
          <div className="metric-label">Available Rooms</div>
        </div>

        <div className="metric-card" style={{ borderLeftColor: getDaysColor(daysSinceFound) }}>
          <div className="metric-value" style={{ color: getDaysColor(daysSinceFound) }}>
            {daysSinceFound}
          </div>
          <div className="metric-label">Days Since Found</div>
          {daysSinceFound !== 'N/A' && (
            <div style={{ 
              fontSize: '0.75rem', 
              color: getDaysColor(daysSinceFound),
              marginTop: '0.25rem',
              fontWeight: '500'
            }}>
              {parseInt(daysSinceFound) <= 7 ? '🆕 New' : 
               parseInt(daysSinceFound) <= 30 ? '📅 Recent' : '⏰ Old'}
            </div>
          )}
        </div>
      </div>

      {/* Property Details */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem' }}>
        
        {/* Basic Information */}
        <div className="card">
          <h3 className="card-title">📋 Property Information</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#64748b' }}>Property ID:</span>
              <span style={{ fontWeight: '500' }}>{property['Property ID'] || 'N/A'}</span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#64748b' }}>Address:</span>
              <span style={{ fontWeight: '500', textAlign: 'right', maxWidth: '60%' }}>
                {property['Full Address'] || 'N/A'}
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#64748b' }}>Postcode:</span>
              <span style={{ fontWeight: '500' }}>{property['Postcode'] || 'N/A'}</span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#64748b' }}>Advertiser:</span>
              <span style={{ fontWeight: '500' }}>{property['Advertiser Name'] || 'N/A'}</span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#64748b' }}>Listing Status:</span>
              <span style={{ fontWeight: '500' }}>{property['Listing Status'] || 'N/A'}</span>
            </div>

          </div>
        </div>

        {/* Rental Details */}
        <div className="card">
          <h3 className="card-title">💰 Rental Details</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#64748b' }}>Bills Included:</span>
              <span style={{ 
                fontWeight: '500',
                color: property['Bills Included']?.toLowerCase() === 'yes' ? '#059669' : '#dc2626'
              }}>
                {property['Bills Included'] || 'N/A'}
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#64748b' }}>Landlord Type:</span>
              <span style={{ fontWeight: '500' }}>{property['Landlord Type'] || 'N/A'}</span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#64748b' }}>Household Gender:</span>
              <span style={{ fontWeight: '500' }}>{property['Household Gender'] || 'N/A'}</span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#64748b' }}>Listed Rooms:</span>
              <span style={{ fontWeight: '500' }}>{property['Listed Rooms'] || 'N/A'}</span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#64748b' }}>Taken Rooms:</span>
              <span style={{ fontWeight: '500' }}>{property['Taken Rooms'] || 'N/A'}</span>
            </div>

          </div>
        </div>
      </div>

      {/* Room Details */}
      {property['Rooms With History'] && property['Rooms With History'].length > 0 ? (
        // Enhanced room display with availability periods
        <div className="card">
          <h3 className="card-title">🏠 Room Breakdown with History</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1rem' }}>
            {property['Rooms With History'].map((room, index) => {
              const isAvailable = room.current_status === 'available';
              const isOffline = room.current_status === 'offline' || !room.is_currently_listed;
              const hasHistory = room.availability_periods && room.availability_periods.length > 0;
              
              return (
                <div 
                  key={room.room_id}
                  style={{
                    padding: '1.5rem',
                    borderRadius: '8px',
                    backgroundColor: isOffline ? '#fef2f2' : isAvailable ? '#f0f9ff' : '#fff7ed',
                    border: `1px solid ${isOffline ? '#fecaca' : isAvailable ? '#bae6fd' : '#fed7aa'}`,
                    opacity: isOffline ? 0.8 : 1
                  }}
                >
                  {/* Room Header */}
                  <div style={{ marginBottom: '1rem' }}>
                    <div style={{ fontWeight: '600', marginBottom: '0.25rem', fontSize: '1.1rem' }}>
                      {room.room_number}
                    </div>
                    <div style={{ color: '#64748b', fontSize: '0.875rem', marginBottom: '0.5rem' }}>
                      {room.price_text} {room.room_type && `(${room.room_type})`}
                    </div>
                    
                    {/* Current Status */}
                    <div style={{ 
                      fontSize: '0.75rem', 
                      marginBottom: '0.5rem',
                      color: isOffline ? '#dc2626' : isAvailable ? '#059669' : '#f59e0b',
                      fontWeight: '500'
                    }}>
                      {isOffline ? '📴 Offline' : isAvailable ? '✅ Available' : '❌ Taken'}
                    </div>
                  </div>

                  {/* Date Gone/Returned Info */}
                  {(room.date_gone || room.date_returned) && (
                    <div style={{ 
                      marginBottom: '1rem',
                      padding: '0.75rem',
                      backgroundColor: 'rgba(255, 255, 255, 0.5)',
                      borderRadius: '6px',
                      fontSize: '0.75rem'
                    }}>
                      {room.date_gone && (
                        <div style={{ marginBottom: '0.25rem' }}>
                          🚫 <strong>Gone:</strong> {room.date_gone}
                        </div>
                      )}
                      {room.date_returned && (
                        <div>
                          ↩️ <strong>Returned:</strong> {room.date_returned}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Period Statistics */}
                  {hasHistory && (
                    <div style={{ 
                      marginBottom: '1rem',
                      padding: '0.75rem',
                      backgroundColor: 'rgba(255, 255, 255, 0.5)',
                      borderRadius: '6px'
                    }}>
                      <div style={{ fontWeight: '500', marginBottom: '0.5rem', fontSize: '0.875rem' }}>
                        📈 Availability History
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                        <div>🔄 {room.total_availability_periods} periods tracked</div>
                        {room.average_availability_duration && (
                          <div>⏱️ Avg: {Math.round(room.average_availability_duration)} days</div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Recent Periods */}
                  {hasHistory && room.availability_periods.slice(0, 3).map((period, pIndex) => (
                    <div 
                      key={period.period_id}
                      style={{
                        padding: '0.5rem',
                        marginBottom: '0.5rem',
                        backgroundColor: period.is_current ? '#dcfce7' : '#f8fafc',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        border: period.is_current ? '1px solid #16a34a' : '1px solid #e2e8f0'
                      }}
                    >
                      <div style={{ fontWeight: '500', marginBottom: '2px' }}>
                        {period.is_current ? '🟢 Current Period' : `📅 Period ${pIndex + 1}`}
                      </div>
                      <div style={{ color: '#64748b' }}>
                        {period.start_date} - {period.end_date || 'ongoing'}
                        {period.duration_days && ` (${period.duration_days} days)`}
                      </div>
                      {period.price_text_at_start && (
                        <div style={{ color: '#059669', fontWeight: '500' }}>
                          {period.price_text_at_start}
                        </div>
                      )}
                    </div>
                  ))}

                  {/* Discovery Info */}
                  <div style={{ 
                    fontSize: '0.75rem', 
                    color: '#64748b',
                    borderTop: '1px solid #e5e7eb',
                    paddingTop: '0.5rem',
                    marginTop: '1rem'
                  }}>
                    <div>📅 First seen: {room.first_seen_date}</div>
                    {room.times_changed > 0 && (
                      <div style={{ marginTop: '2px' }}>
                        🔄 Changed {room.times_changed} time{room.times_changed !== 1 ? 's' : ''}
                      </div>
                    )}
                    {room.days_since_discovered !== null && (
                      <div style={{ marginTop: '2px' }}>
                        ⏰ {room.days_since_discovered} days ago
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : property['All Rooms List'] && property['All Rooms List'].length > 0 && (
        // FALLBACK: Original room display for properties without room tracking
        <div className="card">
          <h3 className="card-title">🏠 Room Breakdown</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
            {property['All Rooms List'].map((room, index) => {
              const isAvailable = !room.includes('(NOW LET)') && room.includes('(');
              
              return (
                <div 
                  key={index}
                  style={{
                    padding: '1rem',
                    borderRadius: '8px',
                    backgroundColor: isAvailable ? '#f0f9ff' : '#fef2f2',
                    border: `1px solid ${isAvailable ? '#bae6fd' : '#fecaca'}`
                  }}
                >
                  <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>
                    {room.split(' - ')[0]} {/* Room number */}
                  </div>
                  <div style={{ color: '#64748b', fontSize: '0.875rem' }}>
                    {room.split(' - ')[1]} {/* Price and type */}
                  </div>
                  <div style={{ 
                    fontSize: '0.75rem', 
                    marginTop: '0.25rem',
                    color: isAvailable ? '#059669' : '#dc2626',
                    fontWeight: '500'
                  }}>
                    {isAvailable ? '✅ Available' : '❌ Taken'}
                  </div>
                  <div style={{ 
                    fontSize: '0.75rem', 
                    marginTop: '0.25rem',
                    color: '#64748b'
                  }}>
                    📅 Found: {property['Date Found'] || property['Analysis Date'] || 'N/A'}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Location */}
      {property['Latitude'] && property['Longitude'] && (
        <div className="card">
          <h3 className="card-title">📍 Location</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#64748b' }}>Coordinates:</span>
              <span style={{ fontWeight: '500' }}>
                {property['Latitude']}, {property['Longitude']}
              </span>
            </div>
            
            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
              <a
                href={`https://www.google.com/maps?q=${property['Latitude']},${property['Longitude']}`}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-secondary"
                style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}
              >
                🗺️ View on Google Maps
              </a>
              <a
                href={`https://maps.apple.com/?ll=${property['Latitude']},${property['Longitude']}&q=${property['Latitude']},${property['Longitude']}`}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-secondary"
                style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}
              >
                🍎 View on Apple Maps
              </a>
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="card">
        <h3 className="card-title">⚡ Quick Actions</h3>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <button 
            onClick={handleExportExcel}
            className="btn btn-primary"
          >
            📄 Download Excel Report
          </button>
          
          {property['URL'] && (
            <a
              href={property['URL']}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-secondary"
            >
              🔗 View Original Listing
            </a>
          )}

          {property['Main Photo URL'] && property['Main Photo URL'] !== 'Not found' && (
            <a
              href={property['Main Photo URL']}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-secondary"
            >
              📷 View Main Photo
            </a>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResultsCard;