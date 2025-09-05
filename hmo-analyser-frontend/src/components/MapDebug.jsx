// src/components/Map.jsx - Improved UI with Professional HMO Registry
import React, { useState, useMemo, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import { propertyApi } from '../utils/api';
import L from 'leaflet';
import MapSearch from '../components/MapSearch';


// Fix Leaflet default markers - CRITICAL for markers to show
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// City configuration for colors and display names (alphabetical order)
const cityConfig = {
  cherwell_banbury: { color: '#8B4513', name: 'Banbury' },
  cherwell_bicester: { color: '#2E8B57', name: 'Bicester' },
  cherwell_kidlington: { color: '#4169E1', name: 'Kidlington' },
  oxford: { color: '#1f77b4', name: 'Oxford' },
  swindon: { color: '#ff7f0e', name: 'Swindon' }
};

// Component to get map reference
const MapRefHandler = ({ onMapReady }) => {
  const map = useMap();
  
  useEffect(() => {
    if (map && onMapReady) {
      onMapReady(map);
    }
  }, [map, onMapReady]);
  
  return null;
};

// Custom marker icons based on property income
const createMarkerIcon = (income) => {
  const color = income > 4000 ? '#10b981' : income > 2000 ? '#f59e0b' : '#ef4444';
  
  return L.divIcon({
    html: `
      <div style="
        background-color: ${color};
        border: 2px solid white;
        border-radius: 50%;
        width: 25px;
        height: 25px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 10px;
        font-weight: bold;
        color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
      ">
        £${Math.round(income / 1000)}k
      </div>
    `,
    className: 'custom-marker',
    iconSize: [25, 25],
    iconAnchor: [12, 12],
  });
};

const Map1 = () => {
  const navigate = useNavigate();
  const [selectedProperty, setSelectedProperty] = useState(null);
  const [filters, setFilters] = useState({
    minIncome: 0,
    maxIncome: 10000,
    billsIncluded: 'all',
    minRooms: 0,
    maxRooms: 20
  });
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  // HMO Registry State
  const [hmoData, setHmoData] = useState({});
  const [hmoVisible, setHmoVisible] = useState({
    cherwell_banbury: false,
    cherwell_bicester: false,
    cherwell_kidlington: false,
    oxford: false,
    swindon: false
  });
  const [hmoLoading, setHmoLoading] = useState({
    cherwell_banbury: false,
    cherwell_bicester: false,
    cherwell_kidlington: false,
    oxford: false,
    swindon: false
  });
  const [hmoStats, setHmoStats] = useState({
    cherwell_banbury: null,
    cherwell_bicester: null,
    cherwell_kidlington: null,
    oxford: null,
    swindon: null
  });
  const mapRef = useRef(null);

  

  // Fetch properties - using your existing API
  const { data: properties = [], isLoading, error } = useQuery({
    queryKey: ['properties'],
    queryFn: propertyApi.getAllProperties,
  });

  console.log('🗺️ Map loaded with', properties.length, 'properties');

  // Fetch HMO data when needed
  const fetchHMOData = async (city) => {
    console.log(`🔘 Fetching ${city} HMO data...`);
    
    if (hmoData[city]) {
      console.log(`🔘 ${city} data already loaded, toggling visibility`);
      toggleHMOVisibility(city);
      return;
    }

    setHmoLoading(prev => ({ ...prev, [city]: true }));
    
    try {
      const response = await fetch(`http://localhost:8001/api/hmo-registry/cities/${city}?enable_geocoding=true`);
      console.log(`🔘 ${city} Response status:`, response.status);
      
      const result = await response.json();
      console.log(`🔘 ${city} Response data:`, result);
      
      if (result.success) {
        console.log(`✅ Loaded ${result.data.length} ${city} HMO properties`);

        setHmoData(prev => ({
          ...prev,
          [city]: result.data
        }));
        
        setHmoStats(prev => ({
          ...prev,
          [city]: result.statistics
        }));
        
        setHmoVisible(prev => ({ ...prev, [city]: true }));
        
        // Add HMO markers to map
        addHMOMarkersToMap(result.data, city);
      } else {
        console.error(`❌ Failed to load ${city} HMO data:`, result);
        alert(`Failed to load ${city} HMO registry data`);
      }
    } catch (error) {
      console.error(`❌ Error fetching ${city} HMO data:`, error);
      alert(`Error loading ${city} HMO registry data`);
    } finally {
      setHmoLoading(prev => ({ ...prev, [city]: false }));
    }
  };

  const toggleHMOVisibility = (city) => {
    if (hmoVisible[city]) {
      removeHMOMarkersFromMap(city);
      setHmoVisible(prev => ({ ...prev, [city]: false }));
    } else {
      if (hmoData[city]) {
        addHMOMarkersToMap(hmoData[city], city);
        setHmoVisible(prev => ({ ...prev, [city]: true }));
      }
    }
  };

  const addHMOMarkersToMap = (data, city) => {
    console.log(`🔧 addHMOMarkersToMap called for ${city} with ${data.length} properties`);
    console.log('🔧 mapRef.current:', mapRef.current);
    
    if (!mapRef.current) {
      console.error('❌ Map reference is null!');
      return;
    }
    
    // Remove existing HMO markers for this city first
    removeHMOMarkersFromMap(city);
    
    const hmoLayer = L.layerGroup();
    const layerKey = `hmoLayer_${city}`;
    
    // Get city-specific border color
    const borderColor = cityConfig[city]?.color || '#1f77b4';

    data.forEach(property => {
      if (property.latitude && property.longitude) {
        // Create custom div icon for HMO markers (stays same size when zooming)
        const statusColor = property.licence_status === 'active' ? '#22c55e' : 
                          property.licence_status === 'expired' ? '#ef4444' : '#6b7280';
        
        const hmoIcon = L.divIcon({
          html: `
            <div style="
              background-color: ${statusColor};
              border: 2px solid ${borderColor};
              border-radius: 50%;
              width: 10px;
              height: 10px;
              opacity: 0.7;
              box-shadow: 0 1px 2px rgba(0,0,0,0.2);
              position: relative;
              z-index: -1;
            "></div>
          `,
          className: 'hmo-marker-background',
          iconSize: [10, 10],
          iconAnchor: [5, 5],
        });

        const marker = L.marker([property.latitude, property.longitude], {
          icon: hmoIcon,
          // Set lower z-index for HMO markers so they appear behind tracked properties
          zIndexOffset: -1000
        });

        const popupContent = `
          <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 320px; line-height: 1.4;">
            <h3 style="color: #1f2937; font-size: 16px; font-weight: 600; margin: 0 0 12px 0; border-bottom: 2px solid ${borderColor}; padding-bottom: 8px;">
              🏛️ ${property.address}
            </h3>
            <div style="margin-bottom: 12px;">
              <div style="margin: 6px 0; font-size: 14px; color: #374151;">
                <strong style="color: #1f2937;">Case:</strong> ${property.case_number || property.id}
              </div>
              <div style="margin: 6px 0; font-size: 14px; color: #374151;">
                <strong style="color: #1f2937;">City:</strong> ${cityConfig[city]?.name || city}
              </div>
              ${property.licence_number ? `<div style="margin: 6px 0; font-size: 14px; color: #374151;"><strong style="color: #1f2937;">License #:</strong> ${property.licence_number}</div>` : ''}
              ${property.postcode ? `<div style="margin: 6px 0; font-size: 14px; color: #374151;"><strong style="color: #1f2937;">Postcode:</strong> ${property.postcode}</div>` : ''}
              ${property.licensee ? `<div style="margin: 6px 0; font-size: 14px; color: #374151;"><strong style="color: #1f2937;">Licensee:</strong> ${property.licensee}</div>` : ''}
              ${property.person_managing ? `<div style="margin: 6px 0; font-size: 14px; color: #374151;"><strong style="color: #1f2937;">Manager:</strong> ${property.person_managing}</div>` : ''}
              ${property.total_occupants ? `<div style="margin: 6px 0; font-size: 14px; color: #374151;"><strong style="color: #1f2937;">Max Occupants:</strong> ${property.total_occupants}</div>` : ''}
              ${property.total_units ? `<div style="margin: 6px 0; font-size: 14px; color: #374151;"><strong style="color: #1f2937;">Units:</strong> ${property.total_units}</div>` : ''}
              ${property.self_contained_flats ? `<div style="margin: 6px 0; font-size: 14px; color: #374151;"><strong style="color: #1f2937;">Self-contained:</strong> ${property.self_contained_flats}</div>` : ''}
              ${property.not_self_contained_flats ? `<div style="margin: 6px 0; font-size: 14px; color: #374151;"><strong style="color: #1f2937;">Shared:</strong> ${property.not_self_contained_flats}</div>` : ''}
              ${property.storeys ? `<div style="margin: 6px 0; font-size: 14px; color: #374151;"><strong style="color: #1f2937;">Storeys:</strong> ${property.storeys}</div>` : ''}
              <div style="margin: 6px 0; font-size: 14px; color: #374151;">
                <strong style="color: #1f2937;">License Status:</strong> 
                <span style="display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; text-transform: uppercase; margin-left: 4px; ${
                  property.licence_status === 'active' ? 'background-color: #dcfce7; color: #166534;' :
                  property.licence_status === 'expired' ? 'background-color: #fef2f2; color: #dc2626;' :
                  'background-color: #f3f4f6; color: #6b7280;'
                }">
                  ${property.licence_status || 'Unknown'}
                </span>
              </div>
              ${property.expiry_date ? `<div style="margin: 6px 0; font-size: 14px; color: #374151;"><strong style="color: #1f2937;">Expires:</strong> ${property.expiry_date}</div>` : ''}
              ${property.licence_expiry_date ? `<div style="margin: 6px 0; font-size: 14px; color: #374151;"><strong style="color: #1f2937;">Expires:</strong> ${new Date(property.licence_expiry_date).toLocaleDateString('en-GB')}</div>` : ''}
            </div>
            <div style="border-top: 1px solid #e5e7eb; padding-top: 8px; margin-top: 12px;">
              <small style="color: #9ca3af; font-size: 11px; font-style: italic;">
                Source: ${cityConfig[city]?.name || city} Council HMO Register
              </small>
            </div>
          </div>
        `;

        marker.bindPopup(popupContent);
        hmoLayer.addLayer(marker);
      }
    });
    
    console.log(`🔧 Created ${city} HMO layer with ${hmoLayer.getLayers().length} markers`);
    
    // Store reference with city-specific key and add to map
    mapRef.current[layerKey] = hmoLayer;
    hmoLayer.addTo(mapRef.current);
    
    console.log(`✅ ${city} HMO markers added to map (underneath tracked properties)`);
  };

  const removeHMOMarkersFromMap = (city) => {
    console.log(`🗑️ Attempting to remove ${city} HMO markers`);
    
    if (!mapRef.current) {
      console.error('❌ Map reference is null when trying to remove markers!');
      return;
    }
    
    const layerKey = `hmoLayer_${city}`;
    
    if (mapRef.current[layerKey]) {
      console.log(`🗑️ Found ${city} layer, removing...`);
      mapRef.current.removeLayer(mapRef.current[layerKey]);
      mapRef.current[layerKey] = null;
      console.log(`✅ ${city} HMO markers removed from map`);
    } else {
      console.log(`⚠️ No ${city} HMO layer found to remove`);
    }
  };

  // Get map reference when MapContainer mounts
  const handleMapCreated = (map) => {
    console.log('🗺️ Map reference created:', map);
    mapRef.current = map;
  };

  // Filter properties based on criteria
  const filteredProperties = useMemo(() => {
    return properties.filter(property => {
      // Only show properties with valid coordinates
      if (!property.latitude || !property.longitude) return false;
      
      // Income filter
      const income = property.monthly_income || 0;
      if (income < filters.minIncome || income > filters.maxIncome) return false;
      
      // Bills filter
      if (filters.billsIncluded !== 'all') {
        const billsIncluded = property.bills_included?.toLowerCase() === 'yes';
        if (filters.billsIncluded === 'yes' && !billsIncluded) return false;
        if (filters.billsIncluded === 'no' && billsIncluded) return false;
      }
      
      // Rooms filter
      const rooms = property.total_rooms || 0;
      if (rooms < filters.minRooms || rooms > filters.maxRooms) return false;
      
      return true;
    });
  }, [properties, filters]);

  // Calculate map center based on properties
  const mapCenter = useMemo(() => {
    if (filteredProperties.length === 0) return [51.7520, -1.2577]; // Oxford center
    
    const avgLat = filteredProperties.reduce((sum, p) => sum + p.latitude, 0) / filteredProperties.length;
    const avgLng = filteredProperties.reduce((sum, p) => sum + p.longitude, 0) / filteredProperties.length;
    
    return [avgLat, avgLng];
  }, [filteredProperties]);

  // Loading state
  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>🗺️</div>
          <div>Loading map with {properties.length > 0 ? properties.length : ''} properties...</div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <div style={{ textAlign: 'center', color: '#ef4444' }}>
          <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>❌</div>
          <div>Failed to load properties: {error.message}</div>
          <button 
            onClick={() => window.location.reload()}
            style={{ 
              marginTop: '1rem', 
              padding: '0.5rem 1rem', 
              backgroundColor: '#3b82f6', 
              color: 'white', 
              border: 'none', 
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ 
      height: 'calc(100vh - 105px)', 
      width: '100vw', 
      position: 'fixed',
      top: '105px',
      left: 0,
      margin: 0, 
      padding: 0,
      zIndex: 10
    }}>
      {/* Sidebar with filters */}
      <div style={{ 
        position: 'absolute',
        top: 0,
        left: sidebarOpen ? 0 : '-100%',
        width: '320px', 
        height: '100vh',
        backgroundColor: 'white', 
        padding: '1rem', 
        borderRight: '1px solid #e5e7eb',
        overflowY: 'auto',
        boxShadow: '2px 0 4px rgba(0,0,0,0.1)',
        zIndex: 1000,
        transition: 'left 0.3s ease-in-out'
      }}>
        <button
          onClick={() => setSidebarOpen(false)}
          style={{
            position: 'absolute',
            top: '1rem',
            right: '1rem',
            background: 'none',
            border: 'none',
            fontSize: '1.5rem',
            cursor: 'pointer',
            color: '#6b7280',
            padding: '0.25rem'
          }}
        >
          ✕
        </button>

        <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1rem', color: '#1f2937', paddingRight: '2rem' }}>
          🏠 Property Map
        </h2>
        
        <div style={{ marginBottom: '1.5rem', padding: '0.75rem', backgroundColor: '#f3f4f6', borderRadius: '8px' }}>
          <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
            Showing <strong>{filteredProperties.length}</strong> of <strong>{properties.length}</strong> properties
          </div>
        </div>

        {/* Property Filters Section */}
        <div style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '0.75rem', color: '#374151' }}>
            🔍 Property Filters
          </h3>
          
          {/* Income Filter */}
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.5rem', color: '#374151' }}>
              Min Monthly Income: £{filters.minIncome.toLocaleString()}
            </label>
            <input
              type="range"
              min="0"
              max="6000"
              step="100"
              value={filters.minIncome}
              onChange={(e) => setFilters(prev => ({ ...prev, minIncome: parseInt(e.target.value) }))}
              style={{ width: '100%', height: '6px', borderRadius: '3px' }}
            />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.5rem', color: '#374151' }}>
              Max Monthly Income: £{filters.maxIncome.toLocaleString()}
            </label>
            <input
              type="range"
              min="0"
              max="10000"
              step="100"
              value={filters.maxIncome}
              onChange={(e) => setFilters(prev => ({ ...prev, maxIncome: parseInt(e.target.value) }))}
              style={{ width: '100%', height: '6px', borderRadius: '3px' }}
            />
          </div>

          {/* Bills Filter */}
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.5rem', color: '#374151' }}>
              Bills Included
            </label>
            <select
              value={filters.billsIncluded}
              onChange={(e) => setFilters(prev => ({ ...prev, billsIncluded: e.target.value }))}
              style={{ 
                width: '100%', 
                padding: '0.5rem', 
                border: '1px solid #d1d5db', 
                borderRadius: '6px',
                fontSize: '0.875rem'
              }}
            >
              <option value="all">All Properties</option>
              <option value="yes">Bills Included</option>
              <option value="no">Bills Not Included</option>
            </select>
          </div>

          {/* Rooms Filter */}
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.5rem', color: '#374151' }}>
              Minimum Rooms: {filters.minRooms}
            </label>
            <input
              type="range"
              min="0"
              max="10"
              value={filters.minRooms}
              onChange={(e) => setFilters(prev => ({ ...prev, minRooms: parseInt(e.target.value) }))}
              style={{ width: '100%', height: '6px', borderRadius: '3px' }}
            />
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.5rem', marginTop: '0.75rem', color: '#374151' }}>
              Maximum Rooms: {filters.maxRooms}
            </label>
            <input
              type="range"
              min="0"
              max="20"
              value={filters.maxRooms}
              onChange={(e) => setFilters(prev => ({ ...prev, maxRooms: parseInt(e.target.value) }))}
              style={{ width: '100%', height: '6px', borderRadius: '3px' }}
            />
          </div>

          {/* Reset Button */}
          <button
            onClick={() => setFilters({ minIncome: 0, maxIncome: 10000, billsIncluded: 'all', minRooms: 0, maxRooms: 20 })}
            style={{ 
              width: '100%', 
              padding: '0.75rem', 
              backgroundColor: '#6b7280', 
              color: 'white', 
              border: 'none', 
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '0.875rem',
              fontWeight: '500'
            }}
          >
            🔄 Reset Filters
          </button>
        </div>

        {/* HMO Registry Section - Moved below filters, professional design */}
        <div style={{ marginBottom: '1.5rem', padding: '1rem', border: '2px solid #e5e7eb', borderRadius: '8px', backgroundColor: '#f9fafb' }}>
          <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '0.75rem', color: '#374151', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            🏛️ HMO Registry
          </h3>
          
          {/* Cities listed alphabetically in consistent format */}
          {Object.entries(cityConfig)
            .sort(([,a], [,b]) => a.name.localeCompare(b.name))
            .map(([cityKey, cityInfo]) => (
            <div key={cityKey} style={{ marginBottom: '1rem', padding: '0.75rem', backgroundColor: 'white', borderRadius: '6px', border: '1px solid #e5e7eb' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <div style={{ width: '12px', height: '12px', backgroundColor: cityInfo.color, borderRadius: '50%' }}></div>
                <span style={{ fontWeight: '600', color: '#1f2937' }}>{cityInfo.name}</span>
              </div>
              
              <button
                onClick={() => fetchHMOData(cityKey)}
                disabled={hmoLoading[cityKey]}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.5rem 0.75rem',
                  backgroundColor: hmoVisible[cityKey] ? '#dc2626' : cityInfo.color,
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: hmoLoading[cityKey] ? 'not-allowed' : 'pointer',
                  fontSize: '0.8rem',
                  fontWeight: '500',
                  width: '100%',
                  opacity: hmoLoading[cityKey] ? 0.6 : 1
                }}
              >
                {hmoLoading[cityKey] ? (
                  <>
                    <div style={{ 
                      width: '12px', 
                      height: '12px', 
                      border: '2px solid #ffffff', 
                      borderTop: '2px solid transparent', 
                      borderRadius: '50%', 
                      animation: 'spin 1s linear infinite' 
                    }}></div>
                    Loading...
                  </>
                ) : hmoVisible[cityKey] ? (
                  <>👁️‍🗨️ Hide {cityInfo.name} HMOs</>
                ) : (
                  <>👁️ Show {cityInfo.name} HMOs</>
                )}
              </button>

              {/* Statistics only show when HMOs are visible */}
              {hmoVisible[cityKey] && hmoStats[cityKey] && (
                <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '0.5rem' }}>
                  <div><strong>{hmoStats[cityKey].total_records?.toLocaleString()}</strong> total ({hmoStats[cityKey].geocoded_records?.toLocaleString()} on map)</div>
                  <div><span style={{ color: '#16a34a' }}>{hmoStats[cityKey].active_licences?.toLocaleString()} active</span>, <span style={{ color: '#dc2626' }}>{hmoStats[cityKey].expired_licences?.toLocaleString()} expired</span></div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Legend */}
        <div style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: '600', marginBottom: '0.75rem', color: '#374151' }}>
            📊 Property Income Legend
          </h3>
          <div style={{ fontSize: '0.8rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem' }}>
              <div style={{ width: '16px', height: '16px', backgroundColor: '#10b981', borderRadius: '50%', marginRight: '0.75rem', border: '2px solid white', boxShadow: '0 1px 2px rgba(0,0,0,0.2)' }}></div>
              <span style={{ color: '#374151' }}>High Income (£4k+)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem' }}>
              <div style={{ width: '16px', height: '16px', backgroundColor: '#f59e0b', borderRadius: '50%', marginRight: '0.75rem', border: '2px solid white', boxShadow: '0 1px 2px rgba(0,0,0,0.2)' }}></div>
              <span style={{ color: '#374151' }}>Medium Income (£2-4k)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <div style={{ width: '16px', height: '16px', backgroundColor: '#ef4444', borderRadius: '50%', marginRight: '0.75rem', border: '2px solid white', boxShadow: '0 1px 2px rgba(0,0,0,0.2)' }}></div>
              <span style={{ color: '#374151' }}>Lower Income (&lt;£2k)</span>
            </div>
          </div>
        </div>
      </div>

      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        style={{
          position: 'absolute',
          top: '1rem',
          left: sidebarOpen ? '340px' : '1rem',
          zIndex: 1001,
          backgroundColor: 'white',
          border: '2px solid #e5e7eb',
          borderRadius: '8px',
          padding: '0.75rem',
          cursor: 'pointer',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
          fontSize: '1rem',
          fontWeight: '600',
          color: '#374151',
          transition: 'left 0.3s ease-in-out',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem'
        }}
      >
        {sidebarOpen ? '◀' : '▶'} 
        {sidebarOpen ? 'Hide' : 'Filters'} 
        {!sidebarOpen && `(${filteredProperties.length})`}
      </button>

      {sidebarOpen && (
        <div
          onClick={() => setSidebarOpen(false)}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.2)',
            zIndex: 999
          }}
        />
      )}

      {/* Map Container */}
      <div style={{ height: '100%', width: '100%' }}>
        <MapContainer
          center={mapCenter}
          zoom={filteredProperties.length > 0 ? 8 : 6}
          style={{ height: '100%', width: '100%' }}
          zoomControl={false}
        >
          <MapRefHandler onMapReady={handleMapCreated} />
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          
          {filteredProperties.map((property) => (
            <Marker
              key={property.property_id}
              position={[property.latitude, property.longitude]}
              icon={createMarkerIcon(property.monthly_income || 0)}
              zIndexOffset={1000}
              eventHandlers={{
                click: () => {
                  setSelectedProperty(property);
                  console.log('🏠 Selected property:', property.address);
                },
              }}
            >
              <Popup maxWidth={300} minWidth={250}>
                <div style={{ padding: '0.5rem' }}>
                  <h3 style={{ fontSize: '1rem', fontWeight: 'bold', marginBottom: '0.75rem', color: '#1f2937' }}>
                    {property.address}
                  </h3>
                  
                  <div style={{ fontSize: '0.875rem', marginBottom: '0.75rem' }}>
                    <div style={{ marginBottom: '0.25rem' }}>
                      <strong>💰 Monthly Income:</strong> £{property.monthly_income?.toLocaleString() || 'N/A'}
                    </div>
                    <div style={{ marginBottom: '0.25rem' }}>
                      <strong>🏠 Total Rooms:</strong> {property.total_rooms || 'N/A'}
                    </div>
                    <div style={{ marginBottom: '0.25rem' }}>
                      <strong>✅ Available Rooms:</strong> {property.available_rooms || 'N/A'}
                    </div>
                    <div style={{ marginBottom: '0.25rem' }}>
                      <strong>💡 Bills Included:</strong> {property.bills_included || 'N/A'}
                    </div>
                    <div style={{ marginBottom: '0.25rem' }}>
                      <strong>👤 Landlord:</strong> {property.advertiser_name || 'N/A'}
                    </div>
                    {property.listing_status && (
                      <div style={{ marginBottom: '0.25rem' }}>
                        <strong>📊 Status:</strong> {property.listing_status}
                      </div>
                    )}
                  </div>
                  
                  <button
                    onClick={() => {
                      console.log('🔗 Navigating to property:', property.property_id);
                      navigate(`/property/${property.property_id}`);
                    }}
                    style={{
                      width: '100%',
                      padding: '0.75rem',
                      backgroundColor: '#3b82f6',
                      color: 'white',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '0.875rem',
                      fontWeight: '500'
                    }}
                  >
                    🔍 View Full Details
                  </button>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>

      {/* Add CSS for spinning animation in global styles */}
      <style dangerouslySetInnerHTML={{
        __html: `
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `
      }} />
    </div>
  );
};

export default Map1;