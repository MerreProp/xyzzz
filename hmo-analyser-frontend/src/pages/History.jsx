import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { propertyApi, downloadFile } from '../utils/api';
import { useNavigate } from 'react-router-dom';

const History = () => {
  const navigate = useNavigate();
  // const navigate = useNavigate(); // Keep this line, just remove the console.log below it
  // Add this helper function at the top of your History component
  // 1. IMPROVED formatDate function - add this to replace the existing one
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    
    try {
      let date;
      
      // Handle different date formats
      if (typeof dateString === 'string' && dateString.includes('/')) {
        // Handle dd/mm/yy format (like "19/07/25")
        const parts = dateString.split('/');
        if (parts.length === 3) {
          const day = parseInt(parts[0], 10);
          const month = parseInt(parts[1], 10) - 1; // JavaScript months are 0-indexed
          let year = parseInt(parts[2], 10);
          
          // Handle 2-digit years (assume 20xx for years 00-99)
          if (year < 100) {
            year += 2000;
          }
          
          date = new Date(year, month, day);
        } else {
          date = new Date(dateString);
        }
      } else {
        // Try to parse as regular date string
        date = new Date(dateString);
      }
      
      // Check if date is valid
      if (isNaN(date.getTime())) {
        return 'Invalid Date';
      }
      
      return date.toLocaleDateString('en-GB', {
        day: '2-digit',
        month: '2-digit',
        year: '2-digit'
      });
    } catch (error) {
      console.error('Error formatting date:', error, 'Input:', dateString);
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

  // 5. DEBUG HELPER - add this temporarily to see what data you're getting
  const debugProperty = (property) => {
    console.log('Property data for debugging:', {
      property_id: property.property_id,
      date_found: property.date_found,
      analysis_date: property.analysis_date,
      created_at: property.created_at,
      available_rooms: property.available_rooms,
      available_rooms_details: property.available_rooms_details,
      address: property.address
    });
  };

  const [sortBy, setSortBy] = useState('analysis_date');
  const [sortOrder, setSortOrder] = useState('desc');
  const [filterBy, setFilterBy] = useState('all');
  const [selectedCity, setSelectedCity] = useState('all');
  const [selectedSuburb, setSelectedSuburb] = useState('all');
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateProgress, setUpdateProgress] = useState(null);

  const queryClient = useQueryClient();

  // Fetch all properties
  const { data: properties = [], isLoading, error, refetch } = useQuery({
    queryKey: ['properties'],
    queryFn: propertyApi.getAllProperties,
  });

  // Update properties mutation
  const updateMutation = useMutation({
    mutationFn: async (propertyIds) => {
      const response = await fetch('/api/properties/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ property_ids: propertyIds })
      });
      return response.json();
    },
    onSuccess: (data) => {
      setUpdateProgress({ taskId: data.task_id, message: data.message });
      // Start polling for update status
      pollUpdateStatus(data.task_id);
    },
    onError: (error) => {
      console.error('Failed to start update:', error);
      alert('Failed to start property updates. Please try again.');
      setIsUpdating(false);
    }
  });

  const getDateGoneDisplay = (dateGone) => {
  if (!dateGone) return '—';
  
  try {
    // Handle different date formats
    const date = new Date(dateGone);
    const now = new Date();
    const daysDiff = Math.floor((now - date) / (1000 * 60 * 60 * 24));
    
    const formattedDate = date.toLocaleDateString('en-GB', {
      day: '2-digit',
      month: '2-digit',
      year: '2-digit'
    });
    
    // Add "days ago" indicator for recent dates
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
    return dateGone;
  }
  };

  // Poll update status
  const pollUpdateStatus = async (taskId) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/api/analysis/${taskId}`);
        const status = await response.json();
        
        setUpdateProgress({
          taskId,
          status: status.status,
          progress: status.progress,
          message: status.status === 'running' ? 
            `Updating properties... ${status.progress?.updated_count || 0} completed` :
            status.status === 'completed' ? 
            `✅ Update completed! ${status.progress?.changes_detected || 0} changes detected` :
            'Update failed'
        });
        
        if (status.status === 'completed' || status.status === 'failed') {
          clearInterval(pollInterval);
          setIsUpdating(false);
          // Refresh the properties list
          queryClient.invalidateQueries(['properties']);
          
          // Clear progress after 5 seconds
          setTimeout(() => setUpdateProgress(null), 5000);
        }
      } catch (error) {
        console.error('Failed to check update status:', error);
        clearInterval(pollInterval);
        setIsUpdating(false);
      }
    }, 2000);
  };

  const handleBulkUpdate = async () => {
    if (window.confirm(`Are you sure you want to update all ${properties.length} properties? This may take several minutes.`)) {
      setIsUpdating(true);
      setUpdateProgress({ message: 'Starting bulk update...' });
      updateMutation.mutate(null); // null means update all properties
    }
  };

  const handleSingleUpdate = async (propertyId) => {
    setIsUpdating(true);
    setUpdateProgress({ message: 'Updating property...' });
    updateMutation.mutate([propertyId]);
  };

  const handleExport = async (propertyId) => {
    try {
      const blob = await propertyApi.exportProperty(propertyId);
      const filename = `hmo_analysis_${propertyId}.xlsx`;
      downloadFile(blob, filename);
    } catch (error) {
      console.error('Failed to export:', error);
      alert('Failed to export Excel file. Please try again.');
    }
  };

  const handleDelete = async (propertyId) => {
    if (window.confirm('Are you sure you want to delete this analysis?')) {
      try {
        await propertyApi.deleteAnalysis(propertyId);
        refetch();
      } catch (error) {
        console.error('Failed to delete:', error);
        alert('Failed to delete analysis. Please try again.');
      }
    }
  };

  // Function to handle row clicks
  const handleRowClick = (propertyId, event) => {
    console.log('🖱️ Row clicked! Property ID:', propertyId);
    console.log('📍 Current URL:', window.location.pathname);
    
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }
    
    try {
      navigate(`/property/${propertyId}`);
      console.log('✅ Navigation called for:', `/property/${propertyId}`);
    } catch (error) {
      console.error('❌ Navigation error:', error);
    }
  };

  // Function to format available rooms with rents
  // 2. IMPROVED formatAvailableRooms function - add this function
  const formatAvailableRooms = (availableRoomsDetails, availableRooms, property) => {
    // ✅ NEW: Use room history data if available (has proper room numbers)
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

    // ✅ FALLBACK: Use legacy availableRoomsDetails (without room numbers)
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

    // Fallback to simple available rooms count
    if (availableRooms && availableRooms > 0) {
      return (
        <div style={{ fontSize: '0.875rem', color: '#059669', fontWeight: '500' }}>
          {availableRooms} available
        </div>
      );
    }

    // No rooms available
    return (
      <span style={{ color: '#64748b', fontSize: '0.875rem' }}>
        No rooms available
      </span>
    );
  };

    // ADD THESE STATE VARIABLES:
  const [cities, setCities] = useState([]);
  const [areas, setAreas] = useState([]);

  // ADD THESE useEffect HOOKS:
  useEffect(() => {
    const fetchCities = async () => {
      try {
        const response = await fetch('/api/filters/cities');
        const data = await response.json();
        setCities(data.cities || []);
      } catch (error) {
        console.error('Error fetching cities:', error);
        setCities([]);
      }
    };

    fetchCities();
  }, []);

  useEffect(() => {
    const fetchAreas = async () => {
      if (selectedCity && selectedCity !== 'all') {
        try {
          const response = await fetch(`/api/filters/areas/${encodeURIComponent(selectedCity)}`);
          const data = await response.json();
          setAreas(data.areas || []);
        } catch (error) {
          console.error('Error fetching areas:', error);
          setAreas([]);
        }
      } else {
        setAreas([]);
      }
    };


    fetchAreas();
  }, [selectedCity]);

    // ADD THE DEBUG CODE RIGHT HERE:
    useEffect(() => {
    if (properties.length > 0) {
      console.log('🔍 Sample property fields:', Object.keys(properties[0]));
      console.log('🔍 Sample property data:', properties[0]);
    }
  }, [properties]);

  // Reset suburb filter when city changes
  const handleCityChange = (newCity) => {
    setSelectedCity(newCity);
    setSelectedSuburb('all');
  };

  // Filter properties by general criteria first
  const generalFilteredProperties = properties.filter(property => {
    if (filterBy === 'all') return true;
    if (filterBy === 'viable') return property.meets_requirements?.toLowerCase().includes('yes');
    if (filterBy === 'non-viable') return !property.meets_requirements?.toLowerCase().includes('yes');
    if (filterBy === 'bills-included') return property.bills_included?.toLowerCase() === 'yes';
    if (filterBy === 'new-today') return property.listing_status?.toLowerCase().includes('new today');
    if (filterBy === 'featured') return property.listing_status?.toLowerCase().includes('featured');
    if (filterBy === 'boosted') return property.listing_status?.toLowerCase().includes('boosted');
    return true;
  });

  // Then filter by location
  const locationFilteredProperties = generalFilteredProperties.filter(property => {
    if (selectedCity === 'all') return true;
    
    // ✅ FIRST: Try using database city field
    if (property.city) {
      if (property.city !== selectedCity) return false;
      
      if (selectedSuburb !== 'all') {
        return property.area === selectedSuburb;
      }
      
      return true;
    }
    
    // ✅ FALLBACK: If no city field, fall back to address parsing
    // console.log('⚠️ Property missing city field, falling back to address parsing:', property.address);
    
    if (!property.address) return false;
    
    const addressParts = property.address.split(',').map(part => part.trim());
    
    // Check if selected city is in the address
    const cityMatch = addressParts.some(part => 
      part.toLowerCase() === selectedCity.toLowerCase()
    );
    
    if (!cityMatch) return false;
    
    // If suburb is selected, check for suburb match
    if (selectedSuburb !== 'all') {
      const suburbMatch = addressParts.some(part => 
        part.toLowerCase() === selectedSuburb.toLowerCase()
      );
      return suburbMatch;
    }
    
    return true;
  });

  // Sort the final filtered properties
  const sortedProperties = [...locationFilteredProperties].sort((a, b) => {
    let aValue = a[sortBy];
    let bValue = b[sortBy];

    // Handle different data types
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

  const getStatusColor = (status) => {
    if (!status) return { bg: '#f1f5f9' };
    
    const statusLower = status.toLowerCase();
    
    if (statusLower.includes('boosted')) {
      return { bg: '#dbeafe' }; // Blue
    } else if (statusLower.includes('new today')) {
      return { bg: '#dcfce7' }; // Green
    } else if (statusLower === 'new') {
      return { bg: '#fed7aa' }; // Orange
    } else if (statusLower.includes('featured')) {
      return { bg: '#fef3c7' }; // Yellow
    } else {
      return { bg: '#f1f5f9' }; // Default gray
    }
  };

  const formatCurrency = (amount) => {
    if (!amount) return 'N/A';
    return `£${Number(amount).toLocaleString()}`;
  };

  const getViabilityBadge = (meets) => {
    if (!meets) return <span className="status-badge">Unknown</span>;
    
    if (meets.toLowerCase().includes('yes')) {
      return <span className="status-badge success">Viable</span>;
    } else {
      return <span className="status-badge error">Issues</span>;
    }
  };

  // ADD THESE FUNCTIONS HERE (after sortedProperties, before return):
  const getFilteredStatsData = () => {
    // Use the same filtered data that's displayed in the table
    const dataForStats = sortedProperties; // This already includes all filters (city, suburb, general filters)
    
    const totalProperties = dataForStats.length;
    const viableProperties = dataForStats.filter(p => 
      p.meets_requirements?.toLowerCase().includes('yes')
    ).length;
    const totalIncome = dataForStats.reduce((sum, p) => 
      sum + (Number(p.monthly_income) || 0), 0
    );
    const updatedProperties = dataForStats.filter(p => p.has_updates).length;
    
    return {
      totalProperties,
      viableProperties,
      totalIncome,
      updatedProperties
    };
  };

  const getLocationContext = () => {
    if (selectedCity === 'all') {
      return 'All Locations';
    } else if (selectedSuburb === 'all') {
      return selectedCity;
    } else {
      return `${selectedSuburb}, ${selectedCity}`;
    }
  };

  // Calculate the stats data
  const { totalProperties, viableProperties, totalIncome, updatedProperties } = getFilteredStatsData();
  const locationContext = getLocationContext();

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem' }}>
        <div className="spinner" style={{ width: '40px', height: '40px', margin: '0 auto 1rem' }}></div>
        <p>Loading property history...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <h2 className="card-title">❌ Error Loading Properties</h2>
        <p style={{ color: '#dc2626', marginBottom: '1rem' }}>
          Failed to load property history. Please check your connection.
        </p>
        <button onClick={() => refetch()} className="btn btn-primary">
          Try Again
        </button>
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
              Property History
            </h1>
            <p style={{ color: '#64748b', fontSize: '1.1rem' }}>
              View and manage all your analyzed properties
            </p>
          </div>
          
          {/* Bulk Update Button */}
          <button
            onClick={handleBulkUpdate}
            disabled={isUpdating || properties.length === 0}
            className="btn btn-primary"
            style={{ 
              backgroundColor: isUpdating ? '#94a3b8' : '#667eea',
              cursor: isUpdating ? 'not-allowed' : 'pointer'
            }}
          >
            {isUpdating ? (
              <>
                <div className="spinner" style={{ width: '16px', height: '16px', marginRight: '0.5rem' }}></div>
                Updating...
              </>
            ) : (
              <>
                🔄 Update All Properties
              </>
            )}
          </button>
        </div>

        {/* Update Progress */}
        {updateProgress && (
          <div style={{ 
            padding: '1rem', 
            backgroundColor: updateProgress.status === 'completed' ? '#dcfce7' : '#fef3c7',
            borderRadius: '8px',
            border: `1px solid ${updateProgress.status === 'completed' ? '#16a34a' : '#f59e0b'}`,
            marginBottom: '1rem'
          }}>
            <div style={{ fontSize: '0.875rem', fontWeight: '500' }}>
              {updateProgress.message}
            </div>
            {updateProgress.progress && (
              <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.25rem' }}>
                Task ID: {updateProgress.taskId}
              </div>
            )}
          </div>
        )}
      </div>

      {/* REPLACE THE OLD SUMMARY STATS WITH THIS DYNAMIC VERSION: */}
      <div style={{ marginBottom: '1rem' }}>
        <h3 style={{ 
          fontSize: '1.2rem', 
          fontWeight: '600', 
          color: '#374151',
          marginBottom: '0.5rem'
        }}>
          📊 Statistics for {locationContext}
        </h3>
        <p style={{ 
          fontSize: '0.875rem', 
          color: '#6b7280',
          marginBottom: '1rem'
        }}>
          {filterBy !== 'all' && `Filtered by: ${filterBy.replace('-', ' ')} • `}
          Updated automatically based on your current filters
        </p>
      </div>

      <div className="results-grid" style={{ marginBottom: '2rem' }}>
        <div className="metric-card">
          <div className="metric-value" style={{ 
            color: totalProperties === 0 ? '#94a3b8' : '#1e293b' 
          }}>
            {totalProperties}
          </div>
          <div className="metric-label">
            {totalProperties === 1 ? 'Property' : 'Properties'}
            {selectedCity !== 'all' && (
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '2px' }}>
                in {locationContext}
              </div>
            )}
          </div>
        </div>
        
        <div className="metric-card">
          <div className="metric-value" style={{ 
            color: viableProperties === 0 ? '#94a3b8' : '#059669' 
          }}>
            {viableProperties}
          </div>
          <div className="metric-label">
            Viable {viableProperties === 1 ? 'Property' : 'Properties'}
            {totalProperties > 0 && (
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '2px' }}>
                {Math.round((viableProperties / totalProperties) * 100)}% success rate
              </div>
            )}
          </div>
        </div>
        
        <div className="metric-card">
          <div className="metric-value" style={{ 
            color: totalIncome === 0 ? '#94a3b8' : '#1e293b' 
          }}>
            {formatCurrency(totalIncome)}
          </div>
          <div className="metric-label">
            Monthly Income
            {totalIncome > 0 && (
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '2px' }}>
                {formatCurrency(totalIncome * 12)} annually
              </div>
            )}
          </div>
        </div>
        
        <div className="metric-card">
          <div className="metric-value" style={{ 
            color: updatedProperties === 0 ? '#94a3b8' : '#f59e0b' 
          }}>
            {updatedProperties}
          </div>
          <div className="metric-label">
            Recently Updated
            {totalProperties > 0 && updatedProperties > 0 && (
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '2px' }}>
                {Math.round((updatedProperties / totalProperties) * 100)}% of properties
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Location-specific insights panel */}
      {selectedCity !== 'all' && totalProperties > 0 && (
        <div className="card" style={{ 
          marginBottom: '2rem',
          backgroundColor: '#f8fafc',
          border: '1px solid #e2e8f0'
        }}>
          <h4 style={{ 
            fontSize: '1rem', 
            fontWeight: '600', 
            color: '#374151',
            marginBottom: '0.75rem'
          }}>
            🎯 {locationContext} Insights
          </h4>
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', 
            gap: '1rem',
            fontSize: '0.875rem'
          }}>
            <div>
              <div style={{ fontWeight: '500', color: '#374151' }}>Average Income</div>
              <div style={{ color: '#6b7280' }}>
                {totalProperties > 0 ? formatCurrency(Math.round(totalIncome / totalProperties)) : 'N/A'}
                {totalProperties > 0 && ' per property'}
              </div>
            </div>
            <div>
              <div style={{ fontWeight: '500', color: '#374151' }}>Success Rate</div>
              <div style={{ color: '#6b7280' }}>
                {totalProperties > 0 ? `${Math.round((viableProperties / totalProperties) * 100)}%` : 'N/A'}
                {totalProperties > 0 && ` (${viableProperties}/${totalProperties})`}
              </div>
            </div>
            <div>
              <div style={{ fontWeight: '500', color: '#374151' }}>Update Status</div>
              <div style={{ color: '#6b7280' }}>
                {updatedProperties > 0 ? `${updatedProperties} recently updated` : 'All properties current'}
              </div>
            </div>
          </div>
        </div>
      )}
      {/* Filters and Controls */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <div>
            <label style={{ fontSize: '0.875rem', color: '#64748b', marginRight: '0.5rem' }}>
              Filter:
            </label>
            <select 
              value={filterBy} 
              onChange={(e) => setFilterBy(e.target.value)}
              style={{ 
                padding: '0.5rem', 
                border: '1px solid #e5e7eb', 
                borderRadius: '6px',
                fontSize: '0.875rem'
              }}
            >
              <option value="all">All Properties</option>
              <option value="viable">Viable Only</option>
              <option value="non-viable">Issues Only</option>
              <option value="bills-included">Bills Included</option>
              <option value="new-today">New Today</option>
              <option value="featured">Featured</option>
              <option value="boosted">Boosted</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.875rem', color: '#64748b', marginRight: '0.5rem' }}>
              City/Town:
            </label>
            <select 
              value={selectedCity} 
              onChange={(e) => handleCityChange(e.target.value)}
              style={{ 
                padding: '0.5rem', 
                border: '1px solid #e5e7eb', 
                borderRadius: '6px',
                fontSize: '0.875rem'
              }}
            >
              <option value="all">All Cities</option>
              {cities.map(city => (
                <option key={city} value={city}>{city}</option>
              ))}
            </select>
          </div>

          {selectedCity !== 'all' && areas.length > 0 && (
            <div>
              <label style={{ fontSize: '0.875rem', color: '#64748b', marginRight: '0.5rem' }}>
                Suburb/Area:
              </label>
              <select 
                value={selectedSuburb} 
                onChange={(e) => setSelectedSuburb(e.target.value)}
                style={{ 
                  padding: '0.5rem', 
                  border: '1px solid #e5e7eb', 
                  borderRadius: '6px',
                  fontSize: '0.875rem'
                }}
              >
                <option value="all">All Areas</option>
                {areas.map(area => (
                  <option key={area} value={area}>{area}</option>
                ))}
              </select>
            </div>
          )}

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
              <option value="advertiser_name">Advertiser</option>
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

          <div style={{ marginLeft: 'auto' }}>
            <Link to="/analyze" className="btn btn-primary">
              ➕ Analyse New Property
            </Link>
          </div>
        </div>

        {/* Show active filters */}
        {(selectedCity !== 'all' || selectedSuburb !== 'all' || filterBy !== 'all') && (
          <div style={{ marginTop: '1rem', padding: '0.75rem', backgroundColor: '#f8fafc', borderRadius: '6px', fontSize: '0.875rem' }}>
            <strong>Active Filters:</strong>
            {filterBy !== 'all' && <span style={{ margin: '0 0.5rem', padding: '2px 6px', backgroundColor: '#e2e8f0', borderRadius: '3px' }}>{filterBy}</span>}
            {selectedCity !== 'all' && <span style={{ margin: '0 0.5rem', padding: '2px 6px', backgroundColor: '#dbeafe', borderRadius: '3px' }}>📍 {selectedCity}</span>}
            {selectedSuburb !== 'all' && <span style={{ margin: '0 0.5rem', padding: '2px 6px', backgroundColor: '#dcfce7', borderRadius: '3px' }}>🏘️ {selectedSuburb}</span>}
            <button 
              onClick={() => {
                setFilterBy('all');
                setSelectedCity('all');
                setSelectedSuburb('all');
              }}
              style={{ 
                marginLeft: '0.5rem', 
                padding: '2px 6px', 
                fontSize: '0.75rem', 
                backgroundColor: '#fee2e2', 
                border: 'none', 
                borderRadius: '3px',
                cursor: 'pointer'
              }}
            >
              Clear All
            </button>
          </div>
        )}
      </div>
      {/* Updated Properties Table */}
      {sortedProperties.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
          <h3 style={{ color: '#64748b', marginBottom: '1rem' }}>No Properties Found</h3>
          <p style={{ color: '#64748b', marginBottom: '2rem' }}>
            {properties.length === 0 
              ? "You haven't analyzed any properties yet." 
              : "No properties match your current filters."
            }
          </p>
          <Link to="/" className="btn btn-primary">
            🔍 Analyze Your First Property
          </Link>
        </div>
      ) : (
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
              {sortedProperties.map((property) => (
                <tr 
                  key={property.property_id}
                  onClick={() => handleRowClick(property.property_id)}
                  style={{ 
                    cursor: 'pointer',
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
                    <div style={{ fontWeight: '500' }}>
                      {property.advertiser_name || 'N/A'}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                      {property.landlord_type || 'Type unknown'}
                    </div>
                  </td>
                  
                  <td>
                    <div style={{ fontSize: '0.875rem' }}>
                      {formatDate(property.date_found || property.analysis_date || property.created_at)}
                    </div>
                    {property.last_updated && property.has_updates && (
                      <div style={{ fontSize: '0.75rem', color: '#059669', fontWeight: '500' }}>
                        Updated: {formatDateTime(property.last_updated)}
                      </div>
                    )}
                  </td>

                  <td>
                    <div style={{ fontSize: '0.875rem' }}>
                      {getDateGoneDisplay(property.date_gone)}
                    </div>
                  </td>
                </tr>
            ))}
          </tbody>
        </table>
      </div>
                  
      )}

      {/* Footer Info - Updated to mention clicking rows */}
      <div style={{ 
        marginTop: '2rem', 
        padding: '1rem', 
        backgroundColor: '#f8fafc', 
        borderRadius: '8px',
        fontSize: '0.875rem',
        color: '#64748b'
      }}>
        💡 <strong>Tip:</strong> Click on any row to view detailed property information and manage updates. Properties show current data from the latest analysis.
      </div>
    </div>
  );
};
      
export default History;