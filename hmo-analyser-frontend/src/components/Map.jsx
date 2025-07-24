import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { propertyApi } from '../utils/api';
import MapUsageTracker from '../utils/mapUsageTracker';
import MapUsageStats from './MapUsageStats';

// Create usage tracker instance
const mapUsageTracker = new MapUsageTracker();

const Map = () => {
  console.log('🗺️ Map component loaded');
  
  // State management
  const [map, setMap] = useState(null);
  const [selectedProperty, setSelectedProperty] = useState(null);
  const [mapStyle, setMapStyle] = useState('mapbox://styles/mapbox/streets-v12');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [filters, setFilters] = useState({
    location: 'all',
    priceRange: [0, 1500],
    roomCount: 'all',
    billsIncluded: 'all',
    availability: 'all',
    requirements: 'all'
  });
  
  const mapContainer = useRef(null);
  const navigate = useNavigate();

  // Fetch all properties using React Query
  const { data: properties = [], isLoading, error, isSuccess } = useQuery({
    queryKey: ['properties'],
    queryFn: propertyApi.getAllProperties,
  });

  // Enhanced debugging
  console.log('🗺️ Map Debug Info:');
  console.log('🗺️ isLoading:', isLoading);
  console.log('🗺️ isSuccess:', isSuccess);
  console.log('🗺️ error:', error);
  console.log('🗺️ Properties fetched:', properties?.length || 0);
  console.log('🗺️ Sample property:', properties?.[0]);
  console.log('🗺️ Token from env:', process.env.REACT_APP_MAPBOX_TOKEN);


  // Filter handlers
  const handleFilterChange = (filterType, value) => {
    setFilters(prev => ({ ...prev, [filterType]: value }));
  };

  const resetFilters = () => {
    setFilters({
      location: 'all',
      priceRange: [0, 1500],
      roomCount: 'all',
      billsIncluded: 'all',
      availability: 'all',
      requirements: 'all'
    });
  };

  // Add marker styles to prevent drift
  useEffect(() => {
    const markerStyles = `
      /* Force 2D rendering */
      .mapboxgl-marker {
        transform-style: flat !important;
      }
      
      /* Disable Mapbox's 3D transforms on markers */
      .mapboxgl-marker > div {
        transform: none !important;
      }
      
      /* Your marker styles */
      .property-marker {
        position: absolute !important;
        top: -25px !important;
        left: -25px !important;
      }
      
      .mapboxgl-marker:hover .property-marker {
        transform: scale(1.1) !important;
        z-index: 1000 !important;
      }
    `;

    const styleElement = document.createElement('style');
    styleElement.textContent = markerStyles;
    document.head.appendChild(styleElement);
    
    return () => {
      document.head.removeChild(styleElement);
    };
  }, []);

useEffect(() => {
  // Add a small delay to ensure DOM is ready
  const initializeMap = () => {
    console.log('🗺️ Map initialization check:');
    console.log('🗺️ mapContainer.current:', !!mapContainer.current);
    console.log('🗺️ window.mapboxgl:', !!window.mapboxgl);
    
    if (!mapContainer.current || !window.mapboxgl) {
      console.log('Map container or Mapbox GL not ready yet, retrying...');
      // Retry after a short delay
      setTimeout(initializeMap, 100);
      return;
    }

    if (!map) {
      console.log('🗺️ Initializing Mapbox map...');
      const initStartTime = Date.now();
      
      const MAPBOX_TOKEN = process.env.REACT_APP_MAPBOX_TOKEN || 'pk.your_mapbox_token_here';
      console.log('🗺️ Using token:', MAPBOX_TOKEN);

      if (MAPBOX_TOKEN === 'pk.your_mapbox_token_here') {
        console.warn('Please set REACT_APP_MAPBOX_TOKEN in your environment variables');
        return;
      }

      const mapboxgl = window.mapboxgl;
      mapboxgl.accessToken = MAPBOX_TOKEN;

      try {
        const newMap = new mapboxgl.Map({
          container: mapContainer.current,
          style: mapStyle,
          center: [-2.5879, 51.4545],
          zoom: 8,
          pitchWithRotate: false,
          dragRotate: false,
          touchZoomRotate: false
        });

        newMap.on('load', () => {
          const loadTime = Date.now() - initStartTime;
          console.log('🗺️ Map loaded successfully in', loadTime, 'ms');
          if (mapUsageTracker) {
            mapUsageTracker.trackMapLoad(mapStyle, loadTime);
          }
          setMap(newMap);
        });

        newMap.on('error', (error) => {
          console.error('🚨 Mapbox error:', error);
        });
        
      } catch (error) {
        console.error('🚨 Map initialization error:', error);
      }
    }
  };

  // Start initialization after a small delay to ensure DOM is ready
  setTimeout(initializeMap, 50);

  return () => {
    if (map) {
      console.log('🗺️ Cleaning up map...');
      map.remove();
    }
  };
}, [mapStyle]); // Removed mapUsageTracker from dependencies to avoid recreation
  // Filter properties with tracking

  // Replace your filteredProperties useMemo with this VSC-friendly version:
const filteredProperties = useMemo(() => {
  console.log('🔍 Bypassing filters - showing all properties:', properties?.length);
  if (!properties || !Array.isArray(properties)) return [];
  
  // TEMPORARY: Return all properties without any filtering to test markers
  return properties;
}, [properties]); // Only depend on properties since we're not using filters right now


  /*const filteredProperties = useMemo(() => {
    console.log('🔍 Bypassing filters - showing all properties:', properties?.length);
    if (!properties || !Array.isArray(properties)) return [];
    
    return properties.filter(property => {
      if (filters.location !== 'all') {
        const addressParts = property.address?.split(',').map(s => s.trim()) || [];
        const city = addressParts.length >= 2 ? 
          addressParts[addressParts.length - 2] : '';
        if (!city.toLowerCase().includes(filters.location.toLowerCase())) {
          return false;
        }
      }

      if (property.monthly_income < filters.priceRange[0] || 
          property.monthly_income > filters.priceRange[1]) {
        return false;
      }

      if (filters.roomCount !== 'all') {
        const roomCount = parseInt(filters.roomCount);
        if (property.total_rooms !== roomCount) {
          return false;
        }
      }

      if (filters.billsIncluded !== 'all') {
        if (filters.billsIncluded === 'yes' && property.bills_included !== 'Yes') {
          return false;
        }
        if (filters.billsIncluded === 'no' && property.bills_included !== 'No') {
          return false;
        }
      }

      if (filters.availability !== 'all') {
        if (filters.availability === 'available' && property.available_rooms === 0) {
          return false;
        }
        if (filters.availability === 'full' && property.available_rooms > 0) {
          return false;
        }
      }

      if (filters.requirements !== 'all') {
        if (filters.requirements === 'meets' && !property.meets_requirements?.includes('Yes')) {
          return false;
        }
        if (filters.requirements === 'doesnt-meet' && property.meets_requirements?.includes('Yes')) {
          return false;
        }
      }

      return true;
    });
    return properties
  }, [properties]); */

  // Track filter usage
  useEffect(() => {
    if (properties && properties.length > 0 && mapUsageTracker) {
      mapUsageTracker.trackFilterUsage('combined', filters, filteredProperties.length);
    }
  }, [filteredProperties.length, filters, properties]);

  // Update map markers with FIXED coordinate and room access
  useEffect(() => {
    if (!map || !properties || properties.length === 0) return;

    const existingMarkers = document.querySelectorAll('.mapboxgl-marker');
    existingMarkers.forEach(marker => marker.remove());

    // Enhanced debugging
    console.log('🗺️ Creating markers for filtered properties:', filteredProperties.length);
    console.log('🔍 Sample property structure:', filteredProperties[0]);
    console.log('🔍 All field names in first property:', filteredProperties[0] ? Object.keys(filteredProperties[0]) : 'No properties');
    
    const propertiesWithCoords = filteredProperties.filter(p => {
      const lat = p.latitude || p.Latitude || p['Latitude'];
      const lon = p.longitude || p.Longitude || p['Longitude'];
      return lat && lon;
    });
    const propertiesWithoutCoords = filteredProperties.filter(p => {
      const lat = p.latitude || p.Latitude || p['Latitude'];
      const lon = p.longitude || p.Longitude || p['Longitude'];
      return !lat || !lon;
    });
    
    console.log(`Properties with coordinates: ${propertiesWithCoords.length}`);
    console.log(`Properties missing coordinates: ${propertiesWithoutCoords.length}`);
    
    if (propertiesWithoutCoords.length > 0) {
      console.log('🚨 Properties missing coordinates:');
      propertiesWithoutCoords.forEach((prop, index) => {
        console.log(`${index + 1}. ${prop.address || 'No address'} (ID: ${prop.property_id})`);
        console.log(`   Available fields:`, Object.keys(prop));
      });
    }

    filteredProperties.forEach(property => {
      // FIXED: Flexible coordinate access to handle different field names
      const lat = property.latitude || property.Latitude || property['Latitude'];
      const lon = property.longitude || property.Longitude || property['Longitude'];
      
      if (!lat || !lon) {
        console.log(`⚠️ Skipping property without coordinates: ${property.address || property.property_id}`);
        return;
      }

      // FIXED: Flexible room count access to handle different field names
      const availableRooms = property.available_rooms || 
                            property['Available Rooms'] || 
                            property.total_rooms || 
                            property['Total Rooms'] || 
                            0;

      // FIXED: Check if property meets requirements using flexible field access
      const meetsRequirements = property.meets_requirements || 
                               property['Meets Requirements'] || 
                               property.meets_requirements?.includes('Yes');

      console.log(`🗺️ Creating marker for property at ${lat}, ${lon} with ${availableRooms} rooms`);

      // Create marker element
      const el = document.createElement('div');
      el.className = 'property-marker';
      el.style.cssText = `
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: red;
        border: 3px solid yellow;
        box-shadow: 0 4px 8px rgba(0,0,0,0.5);
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 16px;
        user-select: none;
        transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
        pointer-events: auto;
      `;
      // FIXED: Display available rooms count
      el.textContent = availableRooms.toString();

      // Create marker with proper coordinates
      const marker = new window.mapboxgl.Marker({
        element: el,
        anchor: 'bottom',
        offset: [0, -25]
        // Add these options to reduce drift
        // pitchAlignment: 'map',
        // rotationAlignment: 'map'
      })
      .setLngLat([lon, lat]);

      // Add click handler
      el.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (mapUsageTracker) {
          mapUsageTracker.trackPropertyInteraction(property.property_id, 'marker_click');
        }
        setSelectedProperty(property);
      });

      // Hover effects
      el.addEventListener('mouseenter', () => {
        el.style.transform = 'scale(1.1)';
        el.style.zIndex = '1000';
        el.style.boxShadow = '0 4px 8px rgba(0,0,0,0.4)';
      });

      el.addEventListener('mouseleave', () => {
        el.style.transform = 'scale(1)';
        el.style.zIndex = '1';
        el.style.boxShadow = '0 2px 4px rgba(0,0,0,0.3)';
      });

      // Add the marker to the map
      marker.addTo(map);
    });

    if (filteredProperties.length > 0) {
      const validProperties = filteredProperties.filter(p => {
        const lat = p.latitude || p.Latitude || p['Latitude'];
        const lon = p.longitude || p.Longitude || p['Longitude'];
        return lat && lon;
      });
      if (validProperties.length > 0) {
        const bounds = new window.mapboxgl.LngLatBounds();
        validProperties.forEach(property => {
          const lat = property.latitude || property.Latitude || property['Latitude'];
          const lon = property.longitude || property.Longitude || property['Longitude'];
          bounds.extend([lon, lat]);
        });
        map.fitBounds(bounds, { padding: 50 });
      }
    }
  }, [map, filteredProperties]);

  // Extract filter options
  const filterOptions = useMemo(() => {
    if (!properties || !Array.isArray(properties)) {
      return { locations: [], roomCounts: [], minPrice: 0, maxPrice: 1500 };
    }

    const locations = [...new Set(properties.map(p => {
      if (!p.address) return '';
      const addressParts = p.address.split(',').map(s => s.trim());
      return addressParts.length >= 2 ? 
        addressParts[addressParts.length - 2] : '';
    }).filter(Boolean))].sort();

    const roomCounts = [...new Set(properties.map(p => p.total_rooms).filter(r => r > 0))].sort((a, b) => a - b);

    const minPrice = Math.min(...properties.map(p => p.monthly_income || 0));
    const maxPrice = Math.max(...properties.map(p => p.monthly_income || 1500));

    return { locations, roomCounts, minPrice, maxPrice };
  }, [properties]);

  // Loading state
  if (isLoading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        flexDirection: 'column',
        gap: '1rem'
      }}>
        <div style={{
          width: '40px',
          height: '40px',
          border: '4px solid #e5e7eb',
          borderTopColor: '#6366f1',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }} />
        <p style={{ color: '#6b7280' }}>Loading properties for map...</p>
        <style>{`
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  // Error state
  if (error) {
    console.error('🚨 API Error details:', error);
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        flexDirection: 'column',
        gap: '1rem'
      }}>
        <div style={{ fontSize: '2rem' }}>❌</div>
        <p style={{ color: '#dc2626' }}>Failed to load properties: {error?.message || 'Unknown error'}</p>
        <p style={{ color: '#9ca3af', fontSize: '0.875rem' }}>
          Check the console for more details
        </p>
        <button 
          onClick={() => window.location.reload()}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: '#6366f1',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  // No properties state
  if (isSuccess && properties.length === 0) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        flexDirection: 'column',
        gap: '1rem'
      }}>
        <div style={{ fontSize: '2rem' }}>📊</div>
        <p style={{ color: '#f59e0b' }}>No properties found in database</p>
        <p style={{ color: '#9ca3af', fontSize: '0.875rem' }}>
          Have you analyzed any properties yet?
        </p>
        <a 
          href="/analyze"
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: '#6366f1',
            color: 'white',
            textDecoration: 'none',
            borderRadius: '6px'
          }}
        >
          Analyze Properties
        </a>
      </div>
    );
  }

  return (
    <div style={{ 
      position: 'relative', 
      height: '100vh',
      overflow: 'hidden',
      background: '#f8fafc'
    }}>
      {/* Main toolbar */}
      <div style={{
        position: 'absolute',
        top: '1rem',
        left: '1rem',
        right: '1rem',
        zIndex: 1000,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        {/* Filter toggle button */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          style={{
            padding: '0.75rem 1.25rem',
            background: 'white',
            border: '2px solid #e5e7eb',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            cursor: 'pointer',
            fontSize: '0.875rem',
            fontWeight: '500',
            color: '#374151',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
            transition: 'all 0.2s'
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="3"></circle>
            <path d="M12 1v6m0 6v6m9-9h-6m-6 0H3m16.24-6.36l-4.24 4.24m-6 2.24l-4.24 4.24m12.48 0l-4.24-4.24m-6-2.24L3.76 7.76"></path>
          </svg>
          <span>Filters</span>
          <span style={{
            background: '#6366f1',
            color: 'white',
            borderRadius: '9999px',
            padding: '0.125rem 0.5rem',
            fontSize: '0.75rem',
            fontWeight: '600'
          }}>
            {filteredProperties.length}
          </span>
        </button>

        {/* Map style selector */}
        <div style={{
          background: 'white',
          borderRadius: '8px',
          display: 'flex',
          gap: '0.5rem',
          padding: '0.5rem',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
        }}>
          <button
            onClick={() => setMapStyle('mapbox://styles/mapbox/streets-v12')}
            style={{
              padding: '0.5rem 1rem',
              background: mapStyle.includes('streets') ? '#6366f1' : 'transparent',
              color: mapStyle.includes('streets') ? 'white' : '#6b7280',
              border: 'none',
              borderRadius: '4px',
              fontSize: '0.75rem',
              fontWeight: '500',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            Streets
          </button>
          <button
            onClick={() => setMapStyle('mapbox://styles/mapbox/satellite-streets-v12')}
            style={{
              padding: '0.5rem 1rem',
              background: mapStyle.includes('satellite') ? '#6366f1' : 'transparent',
              color: mapStyle.includes('satellite') ? 'white' : '#6b7280',
              border: 'none',
              borderRadius: '4px',
              fontSize: '0.75rem',
              fontWeight: '500',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            Satellite
          </button>
        </div>
      </div>

      {/* Sidebar with filters */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: sidebarOpen ? 0 : '-400px',
        width: '350px',
        height: '100%',
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(10px)',
        borderRight: '1px solid #e5e7eb',
        transition: 'left 0.3s ease-in-out',
        zIndex: 2000,
        overflowY: 'auto',
        padding: '5rem 2rem 2rem 2rem'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
          <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: '600', color: '#1f2937' }}>🔍 Filters</h3>
          <button 
            onClick={resetFilters}
            style={{
              padding: '0.5rem 1rem',
              fontSize: '0.75rem',
              background: '#f3f4f6',
              color: '#6b7280',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            Reset All
          </button>
        </div>

        {/* Location Filter */}
        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: '500', color: '#374151' }}>
            📍 Location
          </label>
          <select 
            value={filters.location} 
            onChange={(e) => handleFilterChange('location', e.target.value)}
            style={{ 
              width: '100%',
              padding: '0.75rem', 
              border: '2px solid #e5e7eb', 
              borderRadius: '8px',
              fontSize: '0.875rem',
              color: '#1f2937',
              background: 'white',
              cursor: 'pointer'
            }}
          >
            <option value="all">All Locations</option>
            {filterOptions.locations.map(location => (
              <option key={location} value={location}>{location}</option>
            ))}
          </select>
        </div>

        {/* Price Range Filter */}
        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: '500', color: '#374151' }}>
            💰 Monthly Income: £{filters.priceRange[0]} - £{filters.priceRange[1]}
          </label>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              type="range"
              min={filterOptions.minPrice}
              max={filterOptions.maxPrice}
              value={filters.priceRange[0]}
              onChange={(e) => handleFilterChange('priceRange', [parseInt(e.target.value), filters.priceRange[1]])}
              style={{ flex: 1 }}
            />
            <input
              type="range"
              min={filterOptions.minPrice}
              max={filterOptions.maxPrice}
              value={filters.priceRange[1]}
              onChange={(e) => handleFilterChange('priceRange', [filters.priceRange[0], parseInt(e.target.value)])}
              style={{ flex: 1 }}
            />
          </div>
        </div>

        {/* Room Count Filter */}
        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: '500', color: '#374151' }}>
            🏠 Total Rooms
          </label>
          <select 
            value={filters.roomCount} 
            onChange={(e) => handleFilterChange('roomCount', e.target.value)}
            style={{ 
              width: '100%',
              padding: '0.75rem', 
              border: '2px solid #e5e7eb', 
              borderRadius: '8px',
              fontSize: '0.875rem',
              color: '#1f2937',
              background: 'white',
              cursor: 'pointer'
            }}
          >
            <option value="all">Any Number of Rooms</option>
            {filterOptions.roomCounts.map(count => (
              <option key={count} value={count}>{count} Rooms</option>
            ))}
          </select>
        </div>

        {/* Bills Included Filter */}
        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: '500', color: '#374151' }}>
            💡 Bills Included
          </label>
          <select 
            value={filters.billsIncluded} 
            onChange={(e) => handleFilterChange('billsIncluded', e.target.value)}
            style={{ 
              width: '100%',
              padding: '0.75rem', 
              border: '2px solid #e5e7eb', 
              borderRadius: '8px',
              fontSize: '0.875rem',
              color: '#1f2937',
              background: 'white',
              cursor: 'pointer'
            }}
          >
            <option value="all">Any Bills Option</option>
            <option value="yes">Bills Included</option>
            <option value="no">Bills Not Included</option>
          </select>
        </div>

        {/* Availability Filter */}
        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: '500', color: '#374151' }}>
            🟢 Availability Status
          </label>
          <select 
            value={filters.availability} 
            onChange={(e) => handleFilterChange('availability', e.target.value)}
            style={{ 
              width: '100%',
              padding: '0.75rem', 
              border: '2px solid #e5e7eb', 
              borderRadius: '8px',
              fontSize: '0.875rem',
              color: '#1f2937',
              background: 'white',
              cursor: 'pointer'
            }}
          >
            <option value="all">All Properties</option>
            <option value="available">Has Available Rooms</option>
            <option value="full">Fully Occupied</option>
          </select>
        </div>

        {/* Requirements Filter */}
        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: '500', color: '#374151' }}>
            ✅ Meets Requirements
          </label>
          <select 
            value={filters.requirements} 
            onChange={(e) => handleFilterChange('requirements', e.target.value)}
            style={{ 
              width: '100%',
              padding: '0.75rem', 
              border: '2px solid #e5e7eb', 
              borderRadius: '8px',
              fontSize: '0.875rem',
              color: '#1f2937',
              background: 'white',
              cursor: 'pointer'
            }}
          >
            <option value="all">All Properties</option>
            <option value="meets">Meets Requirements</option>
            <option value="doesnt-meet">Doesn't Meet</option>
          </select>
        </div>

        {/* Stats Summary */}
        <div style={{
          marginTop: '2rem',
          padding: '1rem',
          background: 'white',
          borderRadius: '8px',
          border: '1px solid #e5e7eb'
        }}>
          <h4 style={{ margin: '0 0 0.75rem 0', fontSize: '0.875rem', fontWeight: '600', color: '#374151' }}>
            📊 Filter Summary
          </h4>
          <div style={{ fontSize: '0.75rem', color: '#6b7280', lineHeight: '1.5' }}>
            <div>Showing: <strong>{filteredProperties.length}</strong> of <strong>{properties?.length || 0}</strong> properties</div>
            <div style={{ marginTop: '0.25rem' }}>
              With coordinates: <strong>{filteredProperties.filter(p => {
                const lat = p.latitude || p.Latitude || p['Latitude'];
                const lon = p.longitude || p.Longitude || p['Longitude'];
                return lat && lon;
              }).length}</strong>
            </div>
          </div>
        </div>
      </div>

      {/* Main map container */}
      <div style={{ 
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        zIndex: 1
      }}>
        <div ref={mapContainer} style={{ width: '100%', height: '100%' }}></div>
        
        {/* Property Details Popup */}
        {selectedProperty && (
          <div style={{
            position: 'absolute',
            top: '1rem',
            right: '1rem',
            width: '320px',
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(10px)',
            padding: '1.25rem',
            borderRadius: '12px',
            boxShadow: '0 10px 25px rgba(0, 0, 0, 0.15)',
            border: '1px solid #e2e8f0',
            zIndex: 1500
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
              <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: '600', color: '#1f2937', lineHeight: '1.4' }}>
                {selectedProperty.address || 'Property Details'}
              </h3>
              <button
                onClick={() => setSelectedProperty(null)}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '1.25rem',
                  cursor: 'pointer',
                  color: '#9ca3af',
                  padding: '0.25rem'
                }}
              >
                ×
              </button>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#64748b', fontSize: '0.875rem' }}>Monthly Income:</span>
                <span style={{ fontWeight: '600', color: '#059669' }}>
                  £{selectedProperty.monthly_income || 'N/A'}
                </span>
              </div>
              
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#64748b', fontSize: '0.875rem' }}>Available Rooms:</span>
                <span style={{ fontWeight: '600' }}>
                  {selectedProperty.available_rooms || selectedProperty['Available Rooms'] || '0'} / {selectedProperty.total_rooms || selectedProperty['Total Rooms'] || 'N/A'}
                </span>
              </div>
              
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#64748b', fontSize: '0.875rem' }}>Bills Included:</span>
                <span style={{ 
                  fontWeight: '500',
                  color: selectedProperty.bills_included === 'Yes' ? '#059669' : '#dc2626'
                }}>
                  {selectedProperty.bills_included || selectedProperty['Bills Included'] || 'N/A'}
                </span>
              </div>
              
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#64748b', fontSize: '0.875rem' }}>Meets Requirements:</span>
                <span style={{ 
                  fontWeight: '500',
                  color: selectedProperty.meets_requirements?.includes('Yes') ? '#059669' : '#dc2626'
                }}>
                  {selectedProperty.meets_requirements || selectedProperty['Meets Requirements'] || 'Unknown'}
                </span>
              </div>
            </div>
            
            <button 
              onClick={() => {
                if (mapUsageTracker) {
                  mapUsageTracker.trackPropertyInteraction(selectedProperty.property_id, 'details_link');
                }
                navigate(`/property/${selectedProperty.property_id}`);
              }}
              style={{
                width: '100%',
                padding: '0.75rem 1rem',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '0.875rem',
                fontWeight: '500',
                cursor: 'pointer',
                transition: 'transform 0.2s, box-shadow 0.2s',
                marginTop: '1rem'
              }}
              onMouseEnter={(e) => {
                e.target.style.transform = 'translateY(-1px)';
                e.target.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.4)';
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = 'none';
              }}
            >
              View Full Details →
            </button>
          </div>
        )}



      {/* Usage stats overlay */}
      <MapUsageStats tracker={mapUsageTracker} />
    </div>

            {/* Map not loaded warning */}
        {!map && (
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            background: 'rgba(254, 243, 199, 0.95)',
            backdropFilter: 'blur(10px)',
            padding: '2rem',
            borderRadius: '12px',
            border: '2px solid #f59e0b',
            textAlign: 'center',
            maxWidth: '400px'
          }}>
            <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>🗺️</div>
            <div style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '0.5rem', color: '#92400e' }}>
              Map Configuration Required
            </div>
            <div style={{ fontSize: '0.875rem', color: '#92400e', lineHeight: '1.4' }}>
              To enable the interactive map, you'll need to:
              <br />
              1. Get a free Mapbox access token from <a href="https://mapbox.com" target="_blank" rel="noopener noreferrer" style={{ color: '#059669' }}>mapbox.com</a>
              <br />
              2. Add it to your environment variables as REACT_APP_MAPBOX_TOKEN
            </div>
          </div>
        )}
      </div>
  );
};

export default Map;