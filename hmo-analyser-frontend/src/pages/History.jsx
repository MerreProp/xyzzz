// History.jsx - Enhanced with expandable row functionality
import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { propertyApi, downloadFile } from '../utils/api';
import { useNavigate } from 'react-router-dom';
import { useLastUpdateSummary } from '../hooks/useAnalysis';
import TodaySection from '../components/TodaySection';
import { useTheme } from '../contexts/ThemeContext';
import StatisticsSection from '../components/StatisticsSection';

// UpdateSummary Component
const UpdateSummary = ({ lastUpdateSummary, isLoading }) => {
  const { isDarkMode } = useTheme();
  const [isExpanded, setIsExpanded] = useState(false);

  if (!lastUpdateSummary || isLoading) {
    return null;
  }

  const {
    completed_at,
    total_properties_updated,
    total_changes_detected,
    other_changes = []
  } = lastUpdateSummary;

  const relevantChanges = other_changes.filter(change => {
    const changeType = change.change_type?.toLowerCase();
    return changeType === 'status' || 
           changeType === 'price' || 
           changeType === 'availability' || 
           changeType === 'rooms';
  }).map(change => ({ 
    ...change, 
    type: change.change_type,
    detected_at: change.detected_at || completed_at 
  }));

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
      return dateString || 'Unknown';
    }
  };

  const changesByType = relevantChanges.reduce((acc, change) => {
    const type = change.type?.toLowerCase() || 'other';
    acc[type] = (acc[type] || 0) + 1;
    return acc;
  }, {});

  return (
    <div style={{ 
      marginBottom: '2rem',
      border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
      borderRadius: '12px',
      backgroundColor: isDarkMode ? '#1e293b' : '#ffffff',
      boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
      overflow: 'hidden'
    }}>
      <div 
        onClick={() => setIsExpanded(!isExpanded)}
        style={{
          padding: '1.25rem 1.5rem',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          backgroundColor: isExpanded ? (isDarkMode ? '#334155' : '#f8fafc') : (isDarkMode ? '#1e293b' : '#ffffff'),
          borderBottom: isExpanded ? `1px solid ${isDarkMode ? '#475569' : '#e2e8f0'}` : 'none',
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
              color: isDarkMode ? '#f1f5f9' : '#1e293b'
            }}>
              Last Update Results
            </h3>
            <p style={{ 
              margin: 0, 
              fontSize: '0.875rem', 
              color: isDarkMode ? '#94a3b8' : '#64748b'
            }}>
              {formatDateTime(completed_at)} • {total_properties_updated} properties • {total_changes_detected} changes detected
            </p>
          </div>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {relevantChanges.length > 0 && (
            <div style={{
              backgroundColor: isDarkMode ? 'rgba(220, 38, 38, 0.2)' : '#fee2e2',
              color: '#dc2626',
              padding: '4px 12px',
              borderRadius: '20px',
              fontSize: '0.875rem',
              fontWeight: '500'
            }}>
              {relevantChanges.length} important change{relevantChanges.length !== 1 ? 's' : ''}
            </div>
          )}
          <div style={{
            transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: 'transform 0.3s ease',
            fontSize: '1.4rem',
            color: isDarkMode ? '#94a3b8' : '#64748b'
          }}>
            ▼
          </div>
        </div>
      </div>

      <div style={{
        maxHeight: isExpanded ? '800px' : '0',
        overflow: 'hidden',
        transition: 'max-height 0.4s ease-in-out',
      }}>
        <div style={{ 
          padding: '1.5rem',
          backgroundColor: isDarkMode ? '#1e293b' : '#ffffff'
        }}>
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', 
            gap: '1rem',
            marginBottom: '1.5rem'
          }}>
            <div style={{ 
              textAlign: 'center',
              padding: '1rem',
              backgroundColor: isDarkMode ? '#334155' : '#f8fafc',
              borderRadius: '8px',
              border: `1px solid ${isDarkMode ? '#475569' : '#e2e8f0'}`
            }}>
              <div style={{ fontSize: '1.6rem', fontWeight: 'bold', color: '#3b82f6' }}>
                {total_properties_updated}
              </div>
              <div style={{ fontSize: '0.75rem', color: isDarkMode ? '#94a3b8' : '#64748b' }}>Properties</div>
            </div>
            
            <div style={{ 
              textAlign: 'center',
              padding: '1rem',
              backgroundColor: isDarkMode ? 'rgba(245, 158, 11, 0.1)' : '#fef3c7',
              borderRadius: '8px',
              border: `1px solid ${isDarkMode ? 'rgba(245, 158, 11, 0.3)' : '#f59e0b'}`
            }}>
              <div style={{ fontSize: '1.6rem', fontWeight: 'bold', color: '#d97706' }}>
                {changesByType.price || 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: isDarkMode ? '#94a3b8' : '#64748b' }}>Price Changes</div>
            </div>

            <div style={{ 
              textAlign: 'center',
              padding: '1rem',
              backgroundColor: isDarkMode ? 'rgba(2, 132, 199, 0.1)' : '#e0f2fe',
              borderRadius: '8px',
              border: `1px solid ${isDarkMode ? 'rgba(2, 132, 199, 0.3)' : '#0284c7'}`
            }}>
              <div style={{ fontSize: '1.6rem', fontWeight: 'bold', color: '#0284c7' }}>
                {changesByType.status || 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: isDarkMode ? '#94a3b8' : '#64748b' }}>Status Changes</div>
            </div>

            <div style={{ 
              textAlign: 'center',
              padding: '1rem',
              backgroundColor: isDarkMode ? 'rgba(139, 92, 246, 0.1)' : '#ddd6fe',
              borderRadius: '8px',
              border: `1px solid ${isDarkMode ? 'rgba(139, 92, 246, 0.3)' : '#8b5cf6'}`
            }}>
              <div style={{ fontSize: '1.6rem', fontWeight: 'bold', color: '#8b5cf6' }}>
                {changesByType.availability || 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: isDarkMode ? '#94a3b8' : '#64748b' }}>Availability</div>
            </div>

            <div style={{ 
              textAlign: 'center',
              padding: '1rem',
              backgroundColor: isDarkMode ? 'rgba(229, 62, 62, 0.1)' : '#fed7d7',
              borderRadius: '8px',
              border: `1px solid ${isDarkMode ? 'rgba(229, 62, 62, 0.3)' : '#e53e3e'}`
            }}>
              <div style={{ fontSize: '1.6rem', fontWeight: 'bold', color: '#e53e3e' }}>
                {changesByType.rooms || 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: isDarkMode ? '#94a3b8' : '#64748b' }}>Room Changes</div>
            </div>
          </div>

          {relevantChanges.length === 0 && (
            <div style={{
              textAlign: 'center',
              padding: '2rem',
              backgroundColor: isDarkMode ? 'rgba(16, 163, 74, 0.1)' : '#f0fdf4',
              borderRadius: '8px',
              border: `1px solid ${isDarkMode ? 'rgba(16, 163, 74, 0.3)' : '#16a34a'}`
            }}>
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>✅</div>
              <h4 style={{ 
                color: isDarkMode ? '#4ade80' : '#166534', 
                marginBottom: '0.5rem', 
                fontSize: '1rem' 
              }}>
                No Changes Detected
              </h4>
              <p style={{ 
                color: isDarkMode ? '#4ade80' : '#16a34a', 
                fontSize: '0.875rem',
                margin: 0
              }}>
                All properties remain stable since the last update.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Main History Component
const History = () => {
  const navigate = useNavigate();
  const { isDarkMode, currentPalette } = useTheme();
  const [expandedRow, setExpandedRow] = useState(null);
  const [expandedRowData, setExpandedRowData] = useState(null);
  
  // State variables from history1.jsx
  const [sortBy, setSortBy] = useState('date_found');
  const [sortOrder, setSortOrder] = useState('desc');
  const [filterBy, setFilterBy] = useState('all');
  const [selectedCity, setSelectedCity] = useState('all');
  const [selectedSuburb, setSelectedSuburb] = useState('all');
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateProgress, setUpdateProgress] = useState(null);
  const [cities, setCities] = useState([]);
  const [areas, setAreas] = useState([]);

  // Theme configuration
  const theme = {
    bg: isDarkMode ? '#0f172a' : '#ffffff',
    cardBg: isDarkMode ? '#1e293b' : '#ffffff', 
    text: isDarkMode ? '#f1f5f9' : '#1e293b',
    textSecondary: isDarkMode ? '#94a3b8' : '#64748b',
    border: isDarkMode ? '#334155' : '#e2e8f0',
    accent: currentPalette.primary || '#667eea'
  };

  // Hooks from history1.jsx
  const { data: lastUpdateSummary, isLoading: summaryLoading } = useLastUpdateSummary();
  const queryClient = useQueryClient();

  // Fetch all properties using React Query
  const { data: properties = [], isLoading, error, refetch } = useQuery({
    queryKey: ['properties'],
    queryFn: propertyApi.getAllProperties,
  });

  // Effects
  useEffect(() => {
    fetchCities();
  }, []);

  useEffect(() => {
    fetchAreas();
  }, [selectedCity]);

  useEffect(() => {
    if (properties.length > 0) {
      console.log('🔍 Sample property fields:', Object.keys(properties[0]));
      console.log('🔍 Sample property data:', properties[0]);
    }
  }, [properties]);

  // Fetch cities and areas
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

  // Generate expanded data from existing property data
  const generateExpandedData = (property) => {
    let room_breakdown = [];
    
    if (property['Rooms With History'] && property['Rooms With History'].length > 0) {
      room_breakdown = property['Rooms With History'].map((room, index) => ({
        room_id: room.room_id || index + 1,
        room_number: room.room_number || `Room ${index + 1}`,
        room_type: room.room_type || 'Standard',
        current_price: room.current_price,
        price: room.current_price,
        deposit: room.current_price,
        current_status: room.current_status || 'available',
        status: room.current_status || 'available',
        bills_included: true,
        price_text: room.price_text
      }));
    } else if (property.available_rooms_details && Array.isArray(property.available_rooms_details)) {
      room_breakdown = property.available_rooms_details.map((roomText, index) => {
        const priceMatch = roomText.match(/£(\d+)/);
        const price = priceMatch ? parseInt(priceMatch[1]) : 400;
        
        return {
          room_id: index + 1,
          room_number: `Room ${index + 1}`,
          room_type: roomText.includes('ensuite') ? 'Ensuite' : 'Standard',
          current_price: price,
          price: price,
          deposit: price,
          current_status: 'available',
          status: 'available',
          bills_included: true,
          price_text: roomText
        };
      });
    }

    const analysis_history = [
      {
        date: property.updated_at || property.created_at || new Date().toISOString(),
        monthly_income: property.monthly_income,
        total_income: property.monthly_income,
        available_rooms: property.available_rooms || room_breakdown.length,
        total_available: property.available_rooms || room_breakdown.length,
        changes: property.has_updates ? `Updated analysis - ${property.total_analyses || 1} total analyses` : 'Initial analysis',
        change_summary: property.has_updates ? 'Property data updated' : 'Property first discovered'
      }
    ];

    return {
      room_breakdown,
      analysis_history,
      property_details: {
        advertiser: property.advertiser || property.advertiser_name,
        property_id: property.property_id,
        status: property.listing_status || 'Active',
        last_updated: property.updated_at,
        total_rooms: property.total_rooms,
        available_rooms: property.available_rooms,
        meets_requirements: property.meets_requirements,
        annual_income: property.annual_income
      }
    };
  };

  // Handle row expansion with improved animation
  const handleRowExpansion = (propertyId, event) => {
    event.stopPropagation();
    
    if (expandedRow === propertyId) {
      setExpandedRow(null);
      setExpandedRowData(null);
    } else {
      const property = properties.find(p => p.property_id === propertyId);
      const expandedData = generateExpandedData(property);
      
      setExpandedRow(propertyId);
      setExpandedRowData(expandedData);
    }
  };

  // Handle row click for navigation
  const handleRowClick = (propertyId) => {
    navigate(`/property/${propertyId}`);
  };

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
      pollUpdateStatus(data.task_id);
    },
    onError: (error) => {
      console.error('Failed to start update:', error);
      alert('Failed to start property updates. Please try again.');
      setIsUpdating(false);
    }
  });

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
          queryClient.invalidateQueries(['properties']);
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
      updateMutation.mutate(null);
    }
  };

  const handleCityChange = (newCity) => {
    setSelectedCity(newCity);
    setSelectedSuburb('all');
  };

  // Date formatting functions
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
      return dateGone;
    }
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
    } else if (statusLower.includes('unavailable') || statusLower.includes('expired')) {
      return { bg: '#fee2e2' };
    } else {
      return { bg: '#f1f5f9' };
    }
  };

  // Format currency
  const formatCurrency = (amount) => {
    if (!amount) return 'N/A';
    return `£${Number(amount).toLocaleString()}`;
  };

  // Format available rooms
  const formatAvailableRooms = (availableRoomsDetails, availableRooms, property) => {
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

  // Filtering and sorting logic
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

  const locationFilteredProperties = generalFilteredProperties.filter(property => {
    if (selectedCity === 'all') return true;
    
    if (property.city) {
      if (property.city !== selectedCity) return false;
      
      if (selectedSuburb !== 'all') {
        return property.area === selectedSuburb;
      }
      
      return true;
    }
    
    if (!property.address) return false;
    
    const addressParts = property.address.split(',').map(part => part.trim());
    
    const cityMatch = addressParts.some(part => 
      part.toLowerCase() === selectedCity.toLowerCase()
    );
    
    if (!cityMatch) return false;
    
    if (selectedSuburb !== 'all') {
      const suburbMatch = addressParts.some(part => 
        part.toLowerCase() === selectedSuburb.toLowerCase()
      );
      return suburbMatch;
    }
    
    return true;
  });

  const sortedProperties = [...locationFilteredProperties].sort((a, b) => {
    let aValue = a[sortBy];
    let bValue = b[sortBy];

    if (sortBy === 'monthly_income' || sortBy === 'annual_income' || sortBy === 'total_rooms') {
      aValue = Number(aValue) || 0;
      bValue = Number(bValue) || 0;
    } else if (sortBy === 'date_found') {
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

  // Statistics functions
  const getFilteredStatsData = () => {
    const dataForStats = sortedProperties;
    
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

  const { totalProperties, viableProperties, totalIncome, updatedProperties } = getFilteredStatsData();
  const locationContext = getLocationContext();

  // Render expanded row content with improved animation
  const renderExpandedContent = (property, data) => {
    const isExpanded = expandedRow === property.property_id;
    
    return (
      <tr key={`${property.property_id}-expanded`} className="expanded-row">
        <td colSpan="8" style={{ 
          padding: 0, 
          backgroundColor: theme.cardBg,
          borderBottom: `1px solid ${theme.border}`
        }}>
          <div 
            className="expansion-content"
            style={{
              maxHeight: isExpanded ? '2000px' : '0px',
              overflow: 'hidden',
              transition: 'max-height 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
              backgroundColor: isDarkMode ? '#1e293b' : '#f8fafc'
            }}
          >
            <div style={{
              padding: '1.5rem',
              borderTop: `1px solid ${theme.border}`
            }}>
              
              {/* Header with property name */}
              <div style={{
                marginBottom: '1.5rem',
                paddingBottom: '1rem',
                borderBottom: `1px solid ${theme.border}`
              }}>
                <h3 style={{
                  margin: 0,
                  fontSize: '1.1rem',
                  fontWeight: '600',
                  color: theme.text
                }}>
                  {property.address || 'Property Details'}
                </h3>
                <p style={{
                  margin: '4px 0 0 0',
                  fontSize: '0.875rem',
                  color: theme.textSecondary
                }}>
                  Detailed breakdown and analysis history
                </p>
              </div>

              {/* Three column layout */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                gap: '1.5rem'
              }}>
                
                {/* Room Breakdown Section */}
                <div>
                  <h4 style={{
                    margin: '0 0 1rem 0',
                    fontSize: '1rem',
                    fontWeight: '600',
                    color: theme.text
                  }}>
                    Room Breakdown
                  </h4>
                  
                  {data && data.room_breakdown && data.room_breakdown.length > 0 ? (
                    <div>
                      {data.room_breakdown.map((room, index) => (
                        <div key={room.room_id || index} style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          padding: '0.75rem',
                          backgroundColor: isDarkMode ? '#334155' : '#ffffff',
                          borderRadius: '8px',
                          marginBottom: '0.5rem',
                          border: `1px solid ${theme.border}`
                        }}>
                          <div>
                            <div style={{ 
                              fontWeight: '500', 
                              color: theme.text,
                              fontSize: '0.875rem'
                            }}>
                              {room.room_number} - {room.room_type}
                            </div>
                            <div style={{ 
                              fontSize: '0.75rem', 
                              color: theme.textSecondary 
                            }}>
                              Deposit: {formatCurrency(room.deposit)} • Bills: {room.bills_included ? 'Included' : 'Separate'}
                            </div>
                          </div>
                          
                          <div style={{ textAlign: 'right' }}>
                            <div style={{ 
                              fontWeight: '600', 
                              color: theme.text,
                              fontSize: '0.875rem'
                            }}>
                              {formatCurrency(room.current_price || room.price)}
                            </div>
                            <div style={{
                              fontSize: '0.75rem',
                              fontWeight: '500',
                              color: room.current_status === 'available' || room.status === 'available' ? '#10b981' : '#ef4444'
                            }}>
                              {(room.current_status || room.status || 'Available').charAt(0).toUpperCase() + (room.current_status || room.status || 'Available').slice(1)}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{
                      padding: '2rem',
                      textAlign: 'center',
                      color: theme.textSecondary,
                      fontSize: '0.875rem'
                    }}>
                      No individual room data available for this property
                    </div>
                  )}

                  {/* Monthly Summary */}
                  <div style={{
                    marginTop: '1rem',
                    padding: '0.75rem',
                    backgroundColor: isDarkMode ? '#0f172a' : '#e0f2fe',
                    borderRadius: '8px',
                    border: `1px solid ${theme.accent}40`
                  }}>
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}>
                      <span style={{ 
                        fontWeight: '500', 
                        color: theme.text,
                        fontSize: '0.875rem'
                      }}>
                        Total Monthly Income
                      </span>
                      <span style={{ 
                        fontWeight: '700', 
                        color: theme.accent,
                        fontSize: '1rem'
                      }}>
                        {formatCurrency(property.monthly_income)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Analysis History Section */}
                <div>
                  <h4 style={{
                    margin: '0 0 1rem 0',
                    fontSize: '1rem',
                    fontWeight: '600',
                    color: theme.text
                  }}>
                    Analysis History
                  </h4>

                  {data && data.analysis_history && data.analysis_history.length > 0 ? (
                    data.analysis_history.map((entry, index) => (
                      <div key={index} style={{
                        padding: '0.75rem',
                        backgroundColor: isDarkMode ? '#334155' : '#ffffff',
                        borderRadius: '8px',
                        marginBottom: '0.5rem',
                        border: `1px solid ${theme.border}`
                      }}>
                        <div style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'flex-start',
                          marginBottom: '0.5rem'
                        }}>
                          <div style={{
                            fontSize: '0.875rem',
                            fontWeight: '500',
                            color: theme.text
                          }}>
                            {new Date(entry.date || entry.created_at).toLocaleDateString('en-GB')}
                          </div>
                          <div style={{
                            fontSize: '0.875rem',
                            fontWeight: '600',
                            color: theme.accent
                          }}>
                            {formatCurrency(entry.total_income || entry.monthly_income)}
                          </div>
                        </div>
                        
                        <div style={{
                          fontSize: '0.75rem',
                          color: theme.textSecondary,
                          marginBottom: '0.25rem'
                        }}>
                          Available rooms: {entry.available_rooms || entry.total_available || 0}
                        </div>
                        
                        <div style={{
                          fontSize: '0.75rem',
                          color: theme.text,
                          fontStyle: 'italic'
                        }}>
                          {entry.changes || entry.change_summary || 'No changes detected'}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div style={{
                      padding: '2rem',
                      textAlign: 'center',
                      color: theme.textSecondary,
                      fontSize: '0.875rem'
                    }}>
                      No analysis history available for this property
                    </div>
                  )}

                  {/* Trend indicator */}
                  <div style={{
                    marginTop: '1rem',
                    padding: '0.5rem 0.75rem',
                    backgroundColor: isDarkMode ? '#1e40af20' : '#dbeafe',
                    borderRadius: '8px',
                    border: `1px solid #3b82f640`
                  }}>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      fontSize: '0.875rem',
                      color: '#3b82f6'
                    }}>
                      <strong>Trend:</strong> {property.trend_direction || 'Stable income'}
                    </div>
                  </div>
                </div>

                {/* Property Details Section */}
                <div>
                  <h4 style={{
                    margin: '0 0 1rem 0',
                    fontSize: '1rem',
                    fontWeight: '600',
                    color: theme.text
                  }}>
                    Contact & Property Details
                  </h4>

                  {/* Advertiser Details */}
                  <div style={{
                    padding: '0.75rem',
                    backgroundColor: isDarkMode ? '#334155' : '#ffffff',
                    borderRadius: '8px',
                    marginBottom: '1rem',
                    border: `1px solid ${theme.border}`
                  }}>
                    <div style={{
                      fontSize: '0.875rem',
                      fontWeight: '500',
                      color: theme.text,
                      marginBottom: '0.5rem'
                    }}>
                      Advertiser Information
                    </div>
                    
                    <div style={{ fontSize: '0.75rem', color: theme.textSecondary, lineHeight: '1.4' }}>
                      <div><strong>Platform:</strong> {property.advertiser_name || property.advertiser || 'Unknown'}</div>
                      <div><strong>Property ID:</strong> {property.property_id}</div>
                      <div><strong>Status:</strong> {property.listing_status || 'Active'}</div>
                      <div><strong>Last Updated:</strong> {property.updated_at ? new Date(property.updated_at).toLocaleDateString('en-GB') : 'Unknown'}</div>
                    </div>
                  </div>

                  {/* Property Features */}
                  <div style={{
                    padding: '0.75rem',
                    backgroundColor: isDarkMode ? '#334155' : '#ffffff',
                    borderRadius: '8px',
                    border: `1px solid ${theme.border}`
                  }}>
                    <div style={{
                      fontSize: '0.875rem',
                      fontWeight: '500',
                      color: theme.text,
                      marginBottom: '0.5rem'
                    }}>
                      Property Features
                    </div>
                    
                    <div style={{ fontSize: '0.75rem', color: theme.textSecondary, lineHeight: '1.4' }}>
                      <div><strong>Total Rooms:</strong> {property.total_rooms || 'Unknown'}</div>
                      <div><strong>Available:</strong> {property.available_rooms || 0}</div>
                      <div><strong>Requirements Met:</strong> {property.meets_requirements || 'Unknown'}</div>
                      <div><strong>Annual Income:</strong> {formatCurrency(property.annual_income)}</div>
                    </div>
                  </div>

                  {/* Quick Actions */}
                  <div style={{ marginTop: '1rem' }}>
                    <div style={{
                      display: 'flex',
                      gap: '0.5rem',
                      flexWrap: 'wrap'
                    }}>
                      <button style={{
                        padding: '0.5rem 1rem',
                        fontSize: '0.75rem',
                        borderRadius: '6px',
                        border: `1px solid ${theme.accent}`,
                        backgroundColor: 'transparent',
                        color: theme.accent,
                        cursor: 'pointer',
                        transition: 'all 0.2s'
                      }} onClick={(e) => {
                        e.stopPropagation();
                        handleRowClick(property.property_id);
                      }}>
                        View Full Details
                      </button>
                      
                      <button style={{
                        padding: '0.5rem 1rem',
                        fontSize: '0.75rem',
                        borderRadius: '6px',
                        border: `1px solid ${theme.border}`,
                        backgroundColor: 'transparent',
                        color: theme.textSecondary,
                        cursor: 'pointer',
                        transition: 'all 0.2s'
                      }}>
                        Update Analysis
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </td>
      </tr>
    );
  };

  // Loading and error states
  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem' }}>
        <div style={{
          width: '40px',
          height: '40px',
          border: `3px solid ${theme.border}`,
          borderTop: `3px solid ${theme.accent}`,
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
          margin: '0 auto 1rem'
        }}></div>
        <p style={{ color: theme.text }}>Loading property history...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        backgroundColor: theme.cardBg,
        padding: '2rem',
        borderRadius: '12px',
        border: `1px solid ${theme.border}`,
        textAlign: 'center'
      }}>
        <h2 style={{ color: theme.text, marginBottom: '1rem' }}>❌ Error Loading Properties</h2>
        <p style={{ color: '#dc2626', marginBottom: '1rem' }}>
          Failed to load property history. Please check your connection.
        </p>
        <button 
          onClick={() => refetch()}
          style={{
            padding: '0.75rem 1.5rem',
            backgroundColor: theme.accent,
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer'
          }}
        >
          Try Again
        </button>
      </div>
    );
  }

  // Main render
  return (
    <div style={{ 
      padding: '2rem',
      backgroundColor: theme.bg,
      minHeight: '100vh',
      color: theme.text 
    }}>
      {/* Header with Bulk Update Button */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
          <div>
            <h1 style={{ 
              fontSize: '2rem', 
              fontWeight: 'bold', 
              marginBottom: '0.5rem',
              color: theme.text
            }}>
              Property History
            </h1>
            <p style={{ 
              fontSize: '1.1rem', 
              color: theme.textSecondary 
            }}>
              View and manage all your analyzed properties. Click the expand button to view detailed room breakdowns.
            </p>
          </div>
          
          {/* Bulk Update Button */}
          <button
            onClick={handleBulkUpdate}
            disabled={isUpdating || properties.length === 0}
            style={{ 
              backgroundColor: isUpdating ? '#94a3b8' : theme.accent,
              color: 'white',
              border: 'none',
              padding: '0.75rem 1.5rem',
              borderRadius: '8px',
              cursor: isUpdating ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}
          >
            {isUpdating ? (
              <>
                <div style={{
                  width: '16px',
                  height: '16px',
                  border: '2px solid transparent',
                  borderTop: '2px solid white',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite'
                }}></div>
                Updating...
              </>
            ) : (
              '🔄 Update All Properties'
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

      {/* Update Summary Component */}
      <UpdateSummary 
        lastUpdateSummary={lastUpdateSummary} 
        isLoading={summaryLoading} 
      />

      {/* Statistics Section */}
      <StatisticsSection 
        sortedProperties={sortedProperties}  // Your existing filtered data
        selectedCity={selectedCity}          // Your existing state
        selectedSuburb={selectedSuburb}      // Your existing state  
        filterBy={filterBy}                  // Your existing state
        theme={theme}                        // Your existing theme
        currentPalette={currentPalette}      // Your existing palette
        isDarkMode={isDarkMode}              // Your existing dark mode
      />

      {/* Location-specific insights panel */}
      {selectedCity !== 'all' && totalProperties > 0 && (
        <div style={{ 
          marginBottom: '2rem',
          backgroundColor: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : '#f8fafc',
          border: `1px solid ${theme.border}`,
          padding: '1.5rem',
          borderRadius: '12px'
        }}>
          <h4 style={{ 
            fontSize: '1rem', 
            fontWeight: '600', 
            color: theme.text,
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
              <div style={{ fontWeight: '500', color: theme.text }}>Average Income</div>
              <div style={{ color: theme.textSecondary }}>
                {totalProperties > 0 ? formatCurrency(Math.round(totalIncome / totalProperties)) : 'N/A'}
                {totalProperties > 0 && ' per property'}
              </div>
            </div>
            <div>
              <div style={{ fontWeight: '500', color: theme.text }}>Success Rate</div>
              <div style={{ color: theme.textSecondary }}>
                {totalProperties > 0 ? `${Math.round((viableProperties / totalProperties) * 100)}%` : 'N/A'}
                {totalProperties > 0 && ` (${viableProperties}/${totalProperties})`}
              </div>
            </div>
            <div>
              <div style={{ fontWeight: '500', color: theme.text }}>Update Status</div>
              <div style={{ color: theme.textSecondary }}>
                {updatedProperties > 0 ? `${updatedProperties} recently updated` : 'All properties current'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters and Controls */}
      <div style={{
        backgroundColor: theme.cardBg,
        border: `1px solid ${theme.border}`,
        borderRadius: '12px',
        padding: '1.5rem',
        marginBottom: '2rem'
      }}>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <div>
            <label style={{ fontSize: '0.875rem', color: theme.textSecondary, marginRight: '0.5rem' }}>
              Filter:
            </label>
            <select 
              value={filterBy} 
              onChange={(e) => setFilterBy(e.target.value)}
              style={{ 
                padding: '0.5rem', 
                border: `1px solid ${theme.border}`,
                backgroundColor: theme.cardBg,
                color: theme.text,
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
            <label style={{ fontSize: '0.875rem', color: theme.textSecondary, marginRight: '0.5rem' }}>
              City/Town:
            </label>
            <select 
              value={selectedCity} 
              onChange={(e) => handleCityChange(e.target.value)}
              style={{ 
                padding: '0.5rem', 
                border: `1px solid ${theme.border}`,
                backgroundColor: theme.cardBg,
                color: theme.text,
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
              <label style={{ fontSize: '0.875rem', color: theme.textSecondary, marginRight: '0.5rem' }}>
                Suburb/Area:
              </label>
              <select 
                value={selectedSuburb} 
                onChange={(e) => setSelectedSuburb(e.target.value)}
                style={{ 
                  padding: '0.5rem', 
                  border: `1px solid ${theme.border}`,
                  backgroundColor: theme.cardBg,
                  color: theme.text,
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
            <label style={{ fontSize: '0.875rem', color: theme.textSecondary, marginRight: '0.5rem' }}>
              Sort by:
            </label>
            <select 
              value={sortBy} 
              onChange={(e) => setSortBy(e.target.value)}
              style={{ 
                padding: '0.5rem', 
                border: `1px solid ${theme.border}`,
                backgroundColor: theme.cardBg,
                color: theme.text,
                borderRadius: '6px',
                fontSize: '0.875rem'
              }}
            >
              <option value="date_found">Date Found (Newest First)</option>
              <option value="monthly_income">Monthly Income</option>
              <option value="annual_income">Annual Income</option>
              <option value="total_rooms">Total Rooms</option>
              <option value="address">Address</option>
              <option value="advertiser_name">Advertiser</option>
              <option value="listing_status">Status</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.875rem', color: theme.textSecondary, marginRight: '0.5rem' }}>
              Order:
            </label>
            <select 
              value={sortOrder} 
              onChange={(e) => setSortOrder(e.target.value)}
              style={{ 
                padding: '0.5rem', 
                border: `1px solid ${theme.border}`,
                backgroundColor: theme.cardBg,
                color: theme.text,
                borderRadius: '6px',
                fontSize: '0.875rem'
              }}
            >
              <option value="desc">Descending</option>
              <option value="asc">Ascending</option>
            </select>
          </div>

          <div style={{ marginLeft: 'auto' }}>
            <Link 
              to="/analyze"
              style={{
                padding: '0.75rem 1.5rem',
                backgroundColor: theme.accent,
                color: 'white',
                textDecoration: 'none',
                borderRadius: '8px',
                fontSize: '0.875rem',
                fontWeight: '500',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}
            >
              ➕ Analyse New Property
            </Link>
          </div>
        </div>

        {/* Show active filters */}
        {(selectedCity !== 'all' || selectedSuburb !== 'all' || filterBy !== 'all') && (
          <div style={{ 
            marginTop: '1rem', 
            padding: '0.75rem', 
            backgroundColor: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : '#f8fafc',
            borderRadius: '6px', 
            fontSize: '0.875rem' 
          }}>
            <strong style={{ color: theme.text }}>Active Filters:</strong>
            {filterBy !== 'all' && (
              <span style={{ 
                margin: '0 0.5rem', 
                padding: '2px 6px', 
                backgroundColor: isDarkMode ? '#374151' : '#e2e8f0',
                borderRadius: '3px',
                color: theme.text
              }}>
                {filterBy}
              </span>
            )}
            {selectedCity !== 'all' && (
              <span style={{ 
                margin: '0 0.5rem', 
                padding: '2px 6px', 
                backgroundColor: isDarkMode ? '#1e40af' : '#dbeafe',
                borderRadius: '3px',
                color: isDarkMode ? '#dbeafe' : '#1e40af'
              }}>
                📍 {selectedCity}
              </span>
            )}
            {selectedSuburb !== 'all' && (
              <span style={{ 
                margin: '0 0.5rem', 
                padding: '2px 6px', 
                backgroundColor: isDarkMode ? '#059669' : '#dcfce7',
                borderRadius: '3px',
                color: isDarkMode ? '#dcfce7' : '#059669'
              }}>
                🏘️ {selectedSuburb}
              </span>
            )}
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
                backgroundColor: isDarkMode ? '#dc2626' : '#fee2e2',
                color: isDarkMode ? '#fee2e2' : '#dc2626',
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

      {/* Today Section */}
      <TodaySection />

      {/* Properties Table */}
      {sortedProperties.length === 0 ? (
        <div style={{
          backgroundColor: theme.cardBg,
          border: `1px solid ${theme.border}`,
          borderRadius: '12px',
          textAlign: 'center',
          padding: '3rem'
        }}>
          <h3 style={{ color: theme.textSecondary, marginBottom: '1rem' }}>No Properties Found</h3>
          <p style={{ color: theme.textSecondary, marginBottom: '2rem' }}>
            {properties.length === 0 
              ? "You haven't analyzed any properties yet." 
              : "No properties match your current filters."
            }
          </p>
          <Link 
            to="/analyze"
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: theme.accent,
              color: 'white',
              textDecoration: 'none',
              borderRadius: '8px',
              fontSize: '0.875rem',
              fontWeight: '500',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}
          >
            🔍 Analyze Your First Property
          </Link>
        </div>
      ) : (
        <div style={{
          backgroundColor: theme.cardBg,
          borderRadius: '12px',
          overflow: 'hidden',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)',
          border: `1px solid ${theme.border}`
        }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: isDarkMode ? '#334155' : '#f8fafc' }}>
                <th style={{ 
                  padding: '1rem', 
                  textAlign: 'left', 
                  fontWeight: '600',
                  color: theme.text,
                  borderBottom: `1px solid ${theme.border}`,
                  width: '50px'
                }}>
                  {/* Empty header for expand button column */}
                </th>
                <th style={{ 
                  padding: '1rem', 
                  textAlign: 'left', 
                  fontWeight: '600',
                  color: theme.text,
                  borderBottom: `1px solid ${theme.border}`
                }}>
                  Property
                </th>
                <th style={{ 
                  padding: '1rem', 
                  textAlign: 'left', 
                  fontWeight: '600',
                  color: theme.text,
                  borderBottom: `1px solid ${theme.border}`
                }}>
                  Available Rooms
                </th>
                <th style={{ 
                  padding: '1rem', 
                  textAlign: 'left', 
                  fontWeight: '600',
                  color: theme.text,
                  borderBottom: `1px solid ${theme.border}`
                }}>
                  Monthly Income
                </th>
                <th style={{ 
                  padding: '1rem', 
                  textAlign: 'left', 
                  fontWeight: '600',
                  color: theme.text,
                  borderBottom: `1px solid ${theme.border}`
                }}>
                  Total Rooms
                </th>
                <th style={{ 
                  padding: '1rem', 
                  textAlign: 'left', 
                  fontWeight: '600',
                  color: theme.text,
                  borderBottom: `1px solid ${theme.border}`
                }}>
                  Status
                </th>
                <th style={{ 
                  padding: '1rem', 
                  textAlign: 'left', 
                  fontWeight: '600',
                  color: theme.text,
                  borderBottom: `1px solid ${theme.border}`
                }}>
                  Advertiser
                </th>
                <th style={{ 
                  padding: '1rem', 
                  textAlign: 'left', 
                  fontWeight: '600',
                  color: theme.text,
                  borderBottom: `1px solid ${theme.border}`
                }}>
                  Date Found
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedProperties.map((property) => [
                // Main row
                <tr 
                  key={property.property_id}
                  onClick={() => handleRowClick(property.property_id)}
                  style={{
                    cursor: 'pointer',
                    borderBottom: `1px solid ${theme.border}`,
                    backgroundColor: expandedRow === property.property_id ? 
                      (isDarkMode ? '#334155' : '#f8fafc') : 'transparent',
                    transition: 'background-color 0.2s'
                  }}
                >
                  {/* Expand/Collapse Button */}
                  <td style={{ 
                    padding: '1rem',
                    borderBottom: `1px solid ${theme.border}`,
                    textAlign: 'center'
                  }}>
                    <button
                      onClick={(e) => handleRowExpansion(property.property_id, e)}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        cursor: 'pointer',
                        fontSize: '1.2rem',
                        color: theme.accent,
                        transition: 'transform 0.3s ease',
                        transform: expandedRow === property.property_id ? 
                          'rotate(180deg)' : 'rotate(0deg)',
                        padding: '0.25rem'
                      }}
                    >
                      ▼
                    </button>
                  </td>

                  {/* Property Address */}
                  <td style={{ 
                    padding: '1rem',
                    borderBottom: `1px solid ${theme.border}` 
                  }}>
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

                  {/* Available Rooms */}
                  <td style={{ 
                    padding: '1rem',
                    borderBottom: `1px solid ${theme.border}` 
                  }}>
                    {formatAvailableRooms(property.available_rooms_details, property.available_rooms, property)}
                  </td>
                  
                  {/* Monthly Income */}
                  <td style={{ 
                    padding: '1rem',
                    borderBottom: `1px solid ${theme.border}` 
                  }}>
                    <div style={{ fontWeight: '600' }}>
                      {formatCurrency(property.monthly_income)}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: theme.textSecondary }}>
                      {formatCurrency(property.annual_income)} / year
                    </div>
                  </td>

                  {/* Total Rooms */}
                  <td style={{ 
                    padding: '1rem',
                    borderBottom: `1px solid ${theme.border}`,
                    textAlign: 'center' 
                  }}>
                    <div style={{ 
                      fontSize: '1.5rem', 
                      fontWeight: '500'
                    }}>
                      {property.total_rooms || 'N/A'}
                    </div>
                  </td>

                  {/* Status */}
                  <td style={{ 
                    padding: '1rem',
                    borderBottom: `1px solid ${theme.border}`,
                    textAlign: 'center',
                    verticalAlign: 'middle'
                  }}>
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
                    <div style={{ fontSize: '0.75rem', color: theme.textSecondary, marginTop: '4px', textAlign: 'center' }}>
                      {property.bills_included === 'yes' ? '✅ Bills Inc.' : 
                      property.bills_included === 'no' ? '❌ Bills Not Inc.' : ''}
                    </div>
                  </td>

                  {/* Advertiser */}
                  <td style={{ 
                    padding: '1rem',
                    borderBottom: `1px solid ${theme.border}` 
                  }}>
                    <div style={{ fontWeight: '500' }}>
                      {property.advertiser_name || property.advertiser || 'Unknown'}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: theme.textSecondary }}>
                      {property.landlord_type || 'Type unknown'}
                    </div>
                  </td>

                  {/* Date Found */}
                  <td style={{ 
                    padding: '1rem',
                    borderBottom: `1px solid ${theme.border}` 
                  }}>
                    <div style={{ fontSize: '0.875rem' }}>
                      {formatDate(property.date_found || property.analysis_date || property.created_at)}
                    </div>
                    {property.last_updated && property.has_updates && (
                      <div style={{ fontSize: '0.75rem', color: '#059669', fontWeight: '500' }}>
                        Updated: {formatDateTime(property.last_updated)}
                      </div>
                    )}
                  </td>
                </tr>,
                
                // Expanded row (if this row is expanded)
                ...(expandedRow === property.property_id ? 
                  [renderExpandedContent(property, expandedRowData)] : []
                )
              ]).flat()}
            </tbody>
          </table>
        </div>
      )}

      {/* Footer tip */}
      <div style={{
        marginTop: '1.5rem',
        padding: '1rem',
        backgroundColor: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : '#f8fafc', 
        borderRadius: '12px',
        fontSize: '0.875rem',
        color: theme.textSecondary,
        border: `1px solid ${theme.border}`
      }}>
        <strong style={{ color: theme.text }}>Tip:</strong> Use the expand button to see detailed room breakdowns, analysis history, and property contact information. Click anywhere else on the row to navigate to the full property details page. Properties show current data from the latest analysis.
      </div>

      <style jsx>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        
        button:hover {
          opacity: 0.8;
        }
        
        tr:hover td {
          background-color: transparent !important;
        }

        .expanded-row {
          transition: all 0.5s ease;
        }

        .expansion-content {
          transition: max-height 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        }
      `}</style>
    </div>
  );
};

export default History; 