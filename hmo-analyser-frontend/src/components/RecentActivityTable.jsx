import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Calendar, MapPin, TrendingUp, TrendingDown, Clock, ExternalLink, Filter, RefreshCw, Activity, Search } from 'lucide-react';

// Use your existing API endpoints instead of creating new ones
const fetchAllAnalyses = async () => {
  const response = await fetch('/api/properties');
  if (!response.ok) throw new Error('Failed to fetch properties');
  return response.json();
};

// Utility functions
const formatDate = (dateString) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffInDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
  
  if (diffInDays === 0) return 'Today';
  if (diffInDays === 1) return 'Yesterday';
  if (diffInDays < 7) return `${diffInDays} days ago`;
  if (diffInDays < 30) return `${Math.floor(diffInDays / 7)} weeks ago`;
  if (diffInDays < 365) return `${Math.floor(diffInDays / 30)} months ago`;
  
  return date.toLocaleDateString('en-GB', { 
    day: 'numeric', 
    month: 'short',
    year: 'numeric'
  });
};

const formatCurrency = (amount) => {
  if (!amount) return 'N/A';
  return new Intl.NumberFormat('en-GB', {
    style: 'currency',
    currency: 'GBP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(amount);
};

const getStatusBadge = (status) => {
  const styles = {
    completed: { bg: '#dcfce7', text: '#166534', border: '#bbf7d0' },
    running: { bg: '#fef3c7', text: '#92400e', border: '#fde68a' },
    failed: { bg: '#fee2e2', text: '#991b1b', border: '#fecaca' },
    pending: { bg: '#e0e7ff', text: '#3730a3', border: '#c7d2fe' }
  };
  
  const style = styles[status] || styles.pending;
  
  return (
    <span
      style={{
        padding: '0.25rem 0.5rem',
        fontSize: '0.75rem',
        fontWeight: '500',
        backgroundColor: style.bg,
        color: style.text,
        border: `1px solid ${style.border}`,
        borderRadius: '9999px',
        textTransform: 'capitalize'
      }}
    >
      {status}
    </span>
  );
};

const getChangeIndicator = (changes) => {
  if (!changes || changes.length === 0) {
    return <span style={{ color: '#6b7280', fontSize: '0.875rem' }}>No changes</span>;
  }
  
  const hasSignificantChanges = changes.some(change => 
    ['price_change', 'room_availability_change', 'listing_status_change'].includes(change.change_type)
  );
  
  if (hasSignificantChanges) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: '#dc2626' }}>
        <TrendingUp size={14} />
        <span style={{ fontSize: '0.875rem' }}>{changes.length} changes</span>
      </div>
    );
  }
  
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: '#059669' }}>
      <TrendingDown size={14} />
      <span style={{ fontSize: '0.875rem' }}>{changes.length} minor changes</span>
    </div>
  );
};

const RecentActivityTable = ({ theme, currentPalette, isDarkMode }) => {
  const [selectedDays, setSelectedDays] = useState(3); // Changed default to 3 days
  const [sortBy, setSortBy] = useState('analysis_date');
  const [sortOrder, setSortOrder] = useState('desc');
  const [filterStatus, setFilterStatus] = useState('all');

  const { data: allProperties = [], isLoading, error, refetch, isRefetching } = useQuery({
    queryKey: ['properties'],
    queryFn: fetchAllAnalyses,
    refetchInterval: 30000, // Refresh every 30 seconds
    staleTime: 10000 // Consider data stale after 10 seconds
  });

  // Transform your existing property data into the format we need
  const transformedData = React.useMemo(() => {
    if (!allProperties.length) return [];

    if (allProperties.length > 0) {
        console.log('🔍 DEBUG: First property data:', allProperties[0]);
        console.log('🔍 DEBUG: Available date fields:', Object.keys(allProperties[0]).filter(key => 
            key.toLowerCase().includes('date') || key.toLowerCase().includes('found') || key.toLowerCase().includes('analysis')
        ));
    }
    
    return allProperties.map(property => {
      // Safely get analysis date with fallbacks and validation
        const getValidDate = (dateValue) => {
        if (!dateValue) {
            // Return a very old date for properties without Date Found
            // This prevents them from appearing in recent day filters
            return new Date('2020-01-01'); 
        }
        
        // Handle UK date format (dd/mm/yy or dd/mm/yyyy)
        if (typeof dateValue === 'string' && dateValue.includes('/')) {
            const parts = dateValue.split('/');
            if (parts.length === 3) {
            let [day, month, year] = parts;
            
            // Convert 2-digit year to 4-digit
            if (year.length === 2) {
                year = parseInt(year) > 50 ? `19${year}` : `20${year}`;
            }
            
            // Create date in ISO format (YYYY-MM-DD)
            const isoDate = `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
            const date = new Date(isoDate);
            
            if (!isNaN(date.getTime())) {
                console.log('✅ Parsed UK date:', dateValue, '→', date.toDateString());
                return date;
            }
            }
        }
        
        // Handle other date formats
        const date = new Date(dateValue);
        
        // Check if date is valid
        if (isNaN(date.getTime())) {
            console.warn('Invalid Date Found:', dateValue, 'defaulting to old date');
            return new Date('2020-01-01'); // Return old date instead of current date
        }
        
        return date;
        };
      
      // Try multiple date fields in order of preference
      const analysisDate = getValidDate(property.date_found);
      
      // Calculate days since analysis (safely)
      const now = new Date();
      const diffInDays = Math.floor((now - analysisDate) / (1000 * 60 * 60 * 24));
      
      // Determine status based on your existing data
      let status = 'completed';
      if (property.task_status) {
        status = property.task_status;
      } else if (property['Analysis Date'] || property.analysis_date) {
        status = 'completed';
      } else {
        status = 'pending';
      }
      
      // Calculate analysis duration if available
      let analysis_duration = null;
      if (property.analysis_start && property.analysis_end) {
        try {
          const start = new Date(property.analysis_start);
          const end = new Date(property.analysis_end);
          if (!isNaN(start.getTime()) && !isNaN(end.getTime())) {
            analysis_duration = Math.floor((end - start) / 1000);
          }
        } catch (error) {
          console.warn('Error calculating analysis duration:', error);
        }
      }
      
      // Format changes if available
      const changes = property.recent_changes || [];
      
      return {
        id: property.id || property.property_id || `property-${Math.random()}`,
        task_id: property.task_id,
        property_id: property.id || property.property_id,
        address: property.address || property['Property Address'] || 'Unknown Address',
        postcode: property.postcode || property['Postcode'],
        analysis_date: analysisDate.toISOString(),
        days_ago: Math.max(0, diffInDays), // Ensure non-negative
        status: status,
        monthly_income: property['Monthly Income'] || property.monthly_income,
        total_rooms: property['Total Rooms'] || property.total_rooms,
        listing_status: property['Listing Status'] || property.listing_status || 'Unknown',
        changes: changes,
        advertiser_name: property['Advertiser Name'] || property.advertiser_name,
        analysis_duration: analysis_duration
      };
    });
  }, [allProperties]);

  // Filter data based on selected days (client-side filtering)
  const filteredByDays = React.useMemo(() => {
    if (selectedDays === 9999) {
      // Show all time
      console.log('🔍 Filter: Showing all time -', transformedData.length, 'properties');
      return transformedData;
    }
    
    // Filter by actual days ago
    const filtered = transformedData.filter(item => {
      const daysAgo = item.days_ago;
      return daysAgo <= selectedDays;
    });
    
    console.log(`🔍 Filter: Last ${selectedDays} days - ${filtered.length}/${transformedData.length} properties`);
    console.log('🔍 Sample days ago values:', transformedData.slice(0, 5).map(item => ({ 
      address: item.address?.substring(0, 20) + '...', 
      days_ago: item.days_ago,
      analysis_date: item.analysis_date 
    })));
    
    return filtered;
  }, [transformedData, selectedDays]);

  // Filter and sort data
  const filteredData = filteredByDays
    .filter(item => filterStatus === 'all' || item.status === filterStatus)
    .sort((a, b) => {
      const aVal = a[sortBy];
      const bVal = b[sortBy];
      
      if (sortOrder === 'asc') {
        return aVal > bVal ? 1 : -1;
      } else {
        return aVal < bVal ? 1 : -1;
      }
    });

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const getSortIcon = (field) => {
    if (sortBy !== field) return null;
    return sortOrder === 'asc' ? '↑' : '↓';
  };

  if (error) {
    return (
      <div style={{ 
        padding: '1.5rem', 
        textAlign: 'center', 
        backgroundColor: isDarkMode ? 'rgba(220, 38, 38, 0.1)' : '#fee2e2', 
        border: `1px solid ${isDarkMode ? 'rgba(220, 38, 38, 0.2)' : '#fecaca'}`,
        borderRadius: '8px',
        color: isDarkMode ? '#fca5a5' : '#991b1b'
      }}>
        <p>Failed to load recent activity: {error.message}</p>
        <button 
          onClick={() => refetch()}
          style={{
            marginTop: '1rem',
            padding: '0.5rem 1rem',
            backgroundColor: currentPalette.primary,
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* Header Section - matching your existing style */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h3 style={{
          fontSize: '1.125rem',
          fontWeight: '600',
          color: theme.text,
          marginBottom: '0.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem'
        }}>
          <Activity size={18} style={{ color: currentPalette.primary }} />
          Recent Analysis Activity
        </h3>
        <p style={{
          fontSize: '0.875rem',
          color: theme.textSecondary,
          margin: 0
        }}>
          Properties analyzed over the last {selectedDays === 9999 ? 'all time' : `${selectedDays} days`}
        </p>
      </div>

      {/* Controls Section - matching your form style */}
      <div style={{
        backgroundColor: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : '#f8fafc',
        border: `1px solid ${theme.border}`,
        borderRadius: '8px',
        padding: '1rem',
        marginBottom: '1.5rem'
      }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
          {/* Time Period Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Calendar size={16} style={{ color: theme.textSecondary }} />
            <select
              value={selectedDays}
              onChange={(e) => setSelectedDays(Number(e.target.value))}
              style={{
                padding: '0.5rem',
                border: `1px solid ${theme.border}`,
                borderRadius: '6px',
                fontSize: '0.875rem',
                backgroundColor: theme.cardBg,
                color: theme.text
              }}
            >
              <option value={1}>Last 24 hours</option>
              <option value={3}>Last 3 days</option>
              <option value={7}>Last 7 days</option>
              <option value={14}>Last 14 days</option>
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 3 months</option>
              <option value={365}>Last year</option>
              <option value={9999}>All time</option>
            </select>
          </div>

          {/* Status Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Filter size={16} style={{ color: theme.textSecondary }} />
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              style={{
                padding: '0.5rem',
                border: `1px solid ${theme.border}`,
                borderRadius: '6px',
                fontSize: '0.875rem',
                backgroundColor: theme.cardBg,
                color: theme.text
              }}
            >
              <option value="all">All Status</option>
              <option value="completed">Completed</option>
              <option value="running">Running</option>
              <option value="failed">Failed</option>
              <option value="pending">Pending</option>
            </select>
          </div>

          {/* Refresh Button */}
          <button
            onClick={() => refetch()}
            disabled={isRefetching}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: isRefetching ? theme.border : currentPalette.primary,
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: isRefetching ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              fontSize: '0.875rem'
            }}
          >
            <RefreshCw size={16} style={{ transform: isRefetching ? 'rotate(180deg)' : 'none', transition: 'transform 0.3s' }} />
            {isRefetching ? 'Refreshing...' : 'Refresh'}
          </button>

          {/* Results Count */}
          <div style={{ marginLeft: 'auto', fontSize: '0.875rem', color: theme.textSecondary }}>
            {filteredData.length} properties
          </div>
        </div>
      </div>

      {/* Table Container */}
      {isLoading ? (
        <div style={{ 
          padding: '3rem', 
          textAlign: 'center', 
          color: theme.textSecondary,
          backgroundColor: isDarkMode ? 'rgba(255, 255, 255, 0.02)' : '#f9fafb',
          border: `1px solid ${theme.border}`,
          borderRadius: '8px'
        }}>
          <RefreshCw size={24} style={{ animation: 'spin 1s linear infinite', marginBottom: '1rem' }} />
          <p>Loading recent activity...</p>
        </div>
      ) : filteredData.length === 0 ? (
        <div style={{ 
          padding: '3rem', 
          textAlign: 'center', 
          color: theme.textSecondary,
          backgroundColor: isDarkMode ? 'rgba(255, 255, 255, 0.02)' : '#f9fafb',
          border: `1px solid ${theme.border}`,
          borderRadius: '8px'
        }}>
          <Clock size={48} style={{ marginBottom: '1rem', opacity: 0.5 }} />
          <p>No analyses found for the selected time period</p>
          <p style={{ fontSize: '0.875rem' }}>Try selecting a longer time period or different filters</p>
        </div>
      ) : (
        <div style={{
          backgroundColor: isDarkMode ? 'rgba(255, 255, 255, 0.02)' : '#ffffff',
          border: `1px solid ${theme.border}`,
          borderRadius: '8px',
          overflow: 'hidden'
        }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : '#f9fafb' }}>
                  <th 
                    onClick={() => handleSort('analysis_date')}
                    style={{ 
                      padding: '0.75rem', 
                      textAlign: 'left', 
                      fontSize: '0.875rem', 
                      fontWeight: '600',
                      color: theme.text,
                      cursor: 'pointer',
                      borderBottom: `1px solid ${theme.border}`
                    }}
                  >
                    Date {getSortIcon('analysis_date')}
                  </th>
                  <th 
                    onClick={() => handleSort('address')}
                    style={{ 
                      padding: '0.75rem', 
                      textAlign: 'left', 
                      fontSize: '0.875rem', 
                      fontWeight: '600',
                      color: theme.text,
                      cursor: 'pointer',
                      borderBottom: `1px solid ${theme.border}`
                    }}
                  >
                    Property {getSortIcon('address')}
                  </th>
                  <th 
                    style={{ 
                      padding: '0.75rem', 
                      textAlign: 'left', 
                      fontSize: '0.875rem', 
                      fontWeight: '600',
                      color: theme.text,
                      borderBottom: `1px solid ${theme.border}`
                    }}
                  >
                    Status
                  </th>
                  <th 
                    onClick={() => handleSort('monthly_income')}
                    style={{ 
                      padding: '0.75rem', 
                      textAlign: 'right', 
                      fontSize: '0.875rem', 
                      fontWeight: '600',
                      color: theme.text,
                      cursor: 'pointer',
                      borderBottom: `1px solid ${theme.border}`
                    }}
                  >
                    Income {getSortIcon('monthly_income')}
                  </th>
                  <th 
                    onClick={() => handleSort('total_rooms')}
                    style={{ 
                      padding: '0.75rem', 
                      textAlign: 'center', 
                      fontSize: '0.875rem', 
                      fontWeight: '600',
                      color: theme.text,
                      cursor: 'pointer',
                      borderBottom: `1px solid ${theme.border}`
                    }}
                  >
                    Rooms {getSortIcon('total_rooms')}
                  </th>
                  <th 
                    style={{ 
                      padding: '0.75rem', 
                      textAlign: 'left', 
                      fontSize: '0.875rem', 
                      fontWeight: '600',
                      color: theme.text,
                      borderBottom: `1px solid ${theme.border}`
                    }}
                  >
                    Changes
                  </th>
                  <th 
                    onClick={() => handleSort('advertiser_name')}
                    style={{ 
                      padding: '0.75rem', 
                      textAlign: 'left', 
                      fontSize: '0.875rem', 
                      fontWeight: '600',
                      color: theme.text,
                      cursor: 'pointer',
                      borderBottom: `1px solid ${theme.border}`
                    }}
                  >
                    Source {getSortIcon('advertiser_name')}
                  </th>
                  <th 
                    style={{ 
                      padding: '0.75rem', 
                      textAlign: 'center', 
                      fontSize: '0.875rem', 
                      fontWeight: '600',
                      color: theme.text,
                      borderBottom: `1px solid ${theme.border}`
                    }}
                  >
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredData.map((item, index) => (
                  <tr 
                    key={item.id}
                    style={{ 
                      borderBottom: `1px solid ${theme.border}`,
                      backgroundColor: index % 2 === 0 ? 'transparent' : (isDarkMode ? 'rgba(255, 255, 255, 0.02)' : '#f9fafb')
                    }}
                  >
                    <td style={{ padding: '1rem 0.75rem' }}>
                      <div style={{ fontSize: '0.875rem', color: theme.text }}>
                        {formatDate(item.analysis_date)}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: theme.textSecondary }}>
                        {new Date(item.analysis_date).toLocaleTimeString('en-GB', { 
                          hour: '2-digit', 
                          minute: '2-digit' 
                        })}
                      </div>
                    </td>
                    <td style={{ padding: '1rem 0.75rem' }}>
                      <div style={{ fontSize: '0.875rem', color: theme.text, fontWeight: '500' }}>
                        {item.address}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: theme.textSecondary, display: 'flex', alignItems: 'center', gap: '0.25rem', marginTop: '0.25rem' }}>
                        <MapPin size={12} />
                        {item.postcode}
                      </div>
                    </td>
                    <td style={{ padding: '1rem 0.75rem' }}>
                      {getStatusBadge(item.status)}
                      {item.analysis_duration && (
                        <div style={{ fontSize: '0.75rem', color: theme.textSecondary, marginTop: '0.25rem' }}>
                          {item.analysis_duration}s
                        </div>
                      )}
                    </td>
                    <td style={{ padding: '1rem 0.75rem', textAlign: 'right' }}>
                      <div style={{ fontSize: '0.875rem', color: theme.text, fontWeight: '500' }}>
                        {formatCurrency(item.monthly_income)}
                      </div>
                    </td>
                    <td style={{ padding: '1rem 0.75rem', textAlign: 'center' }}>
                      <div style={{ fontSize: '0.875rem', color: theme.text, fontWeight: '500' }}>
                        {item.total_rooms || '-'}
                      </div>
                    </td>
                    <td style={{ padding: '1rem 0.75rem' }}>
                      {getChangeIndicator(item.changes)}
                    </td>
                    <td style={{ padding: '1rem 0.75rem' }}>
                      <div style={{ fontSize: '0.875rem', color: theme.text }}>
                        {item.advertiser_name || 'Unknown'}
                      </div>
                    </td>
                    <td style={{ padding: '1rem 0.75rem', textAlign: 'center' }}>
                      <button
                        onClick={() => window.open(`/property/${item.property_id}`, '_blank')}
                        style={{
                          padding: '0.25rem 0.5rem',
                          backgroundColor: currentPalette.primary,
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '0.75rem',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.25rem'
                        }}
                      >
                        <ExternalLink size={12} />
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default RecentActivityTable;