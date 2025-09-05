// src/components/Map.jsx - Improved UI with Professional HMO Registry
import React, { useState, useMemo, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import { propertyApi } from '../utils/api';
import L from 'leaflet';
import MapSearch from '../components/MapSearch';
import { useTheme } from '../contexts/ThemeContext';
import { useDarkMode } from '../contexts/DarkModeContext';
import { Filter, X, Search } from 'lucide-react';



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
  swindon: { color: '#ff7f0e', name: 'Swindon' },
    // Vale of White Horse towns
  vale_abingdon: {
    name: 'Abingdon',
    color: '#8B4513',  // Brown shade
    parent: 'Vale of White Horse',
    region: 'Oxfordshire'
  },
  vale_botley: {
    name: 'Botley', 
    color: '#A0522D',  // Darker brown
    parent: 'Vale of White Horse',
    region: 'Oxfordshire'
  },
  vale_kennington: {
    name: 'Kennington',
    color: '#CD853F',  // Peru color
    parent: 'Vale of White Horse',
    region: 'Oxfordshire'
  },
  vale_wantage: {
    name: 'Wantage',
    color: '#D2691E',  // Chocolate
    parent: 'Vale of White Horse',
    region: 'Oxfordshire'
  },
  vale_other: {
    name: 'Vale Other Areas',
    color: '#F4A460',  // Sandy brown
    parent: 'Vale of White Horse',
    region: 'Oxfordshire'
  },

  // South Oxfordshire towns  
  south_didcot: {
    name: 'Didcot',
    color: '#4682B4',  // Steel blue
    parent: 'South Oxfordshire',
    region: 'Oxfordshire'
  },
  south_henley: {
    name: 'Henley-on-Thames',
    color: '#5F9EA0',  // Cadet blue  
    parent: 'South Oxfordshire',
    region: 'Oxfordshire'
  },
  south_thame: {
    name: 'Thame',
    color: '#6495ED',  // Cornflower blue
    parent: 'South Oxfordshire', 
    region: 'Oxfordshire'
  },
  south_wallingford: {
    name: 'Wallingford',
    color: '#708090',  // Slate gray
    parent: 'South Oxfordshire',
    region: 'Oxfordshire'
  },
  south_other: {
    name: 'South Oxon Other Areas',
    color: '#778899',  // Light slate gray
    parent: 'South Oxfordshire',
    region: 'Oxfordshire'
  }
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

const useSidebarState = () => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  
  useEffect(() => {
    const checkSidebarState = () => {
      // Check the actual sidebar element's width
      const sidebar = document.querySelector('div[style*="width: 80px"], div[style*="width: 280px"]');
      if (sidebar) {
        const style = sidebar.getAttribute('style');
        setSidebarCollapsed(style.includes('width: 80px'));
      }
    };

    checkSidebarState();
    const interval = setInterval(checkSidebarState, 100);
    return () => clearInterval(interval);
  }, []);

  return sidebarCollapsed;
};

const Map = () => {
  const { currentPalette } = useTheme();
  const { isDarkMode } = useDarkMode();

  const baseColors = {
    darkSlate: '#2C3E4A',
    lightCream: '#F5F1E8',
    softGray: '#A8A5A0',
  };

  // Theme configuration matching Layout.jsx
  const theme = isDarkMode ? {
    sidebarBg: `linear-gradient(180deg, ${baseColors.darkSlate} 0%, #1e3a47 100%)`,
    mainBg: '#1a2b32',
    cardBg: '#2c3e4a',
    topBarBg: baseColors.darkSlate,
    text: baseColors.lightCream,
    textSecondary: currentPalette.secondary,
    border: 'rgba(180, 180, 180, 0.2)',
    accent: currentPalette.primary,
    accentHover: currentPalette.secondary
  } : {
    sidebarBg: `linear-gradient(180deg, ${currentPalette.primary} 0%, ${currentPalette.secondary} 100%)`,
    mainBg: baseColors.lightCream,
    cardBg: '#ffffff',
    topBarBg: 'white',
    text: baseColors.darkSlate,
    textSecondary: baseColors.softGray,
    border: 'rgba(168, 165, 160, 0.3)',
    accent: currentPalette.accent,
    accentHover: currentPalette.primary
  };
  const sidebarCollapsed = useSidebarState();
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
    swindon: false,
    vale_abingdon: false,
    vale_botley: false,
    vale_kennington: false,
    vale_wantage: false,
    vale_other: false,
    south_didcot: false,
    south_henley: false,
    south_thame: false,
    south_wallingford: false,
    south_other: false,
  });
  const [hmoLoading, setHmoLoading] = useState({
    cherwell_banbury: false,
    cherwell_bicester: false,
    cherwell_kidlington: false,
    oxford: false,
    swindon: false,
    vale_abingdon: false,
    vale_botley: false,
    vale_kennington: false,
    vale_wantage: false,
    vale_other: false,
    south_didcot: false,
    south_henley: false,
    south_thame: false,
    south_wallingford: false,
    south_other: false
  });
  const [hmoStats, setHmoStats] = useState({
    cherwell_banbury: null,
    cherwell_bicester: null,
    cherwell_kidlington: null,
    oxford: null,
    swindon: null,
    vale_abingdon: null,
    vale_botley: null,
    vale_kennington: null,
    vale_wantage: null,
    vale_other: null,
    south_didcot: null,
    south_henley: null,
    south_thame: null,
    south_wallingford: null,
    south_other: null
  });
  const mapRef = useRef(null);

  // Search state variables
  const [searchSelectedMarker, setSearchSelectedMarker] = useState(null);
  const [mapCenter, setMapCenter] = useState([51.7520, -1.2577]); // Oxford center as default
  const [mapZoom, setMapZoom] = useState(10);

  // Fetch properties - using your existing API
  const { data: properties = [], isLoading, error } = useQuery({
    queryKey: ['properties'],
    queryFn: propertyApi.getAllProperties,
  });

  console.log('🗺️ Map loaded with', properties.length, 'properties');

  // Search handler functions
  const handleSearchResultSelect = (result) => {
    console.log('Search result selected:', result);
    
    // Set the selected marker for highlighting
    setSearchSelectedMarker(result);
    
    // Clear the selection after 5 seconds
    setTimeout(() => {
      setSearchSelectedMarker(null);
    }, 5000);
    
    // If it's a tracked property, also set it as selected
    if (result.type === 'tracked_property') {
      setSelectedProperty(result.data);
    }
  };

  const handleMapCenter = (coordinates, zoom = 15) => {
    console.log('Centering map on:', coordinates, 'zoom:', zoom);
    setMapCenter(coordinates);
    setMapZoom(zoom);
    
    // If you have direct access to the map instance, you can also do:
    if (mapRef.current) {
      mapRef.current.setView(coordinates, zoom);
    }
  };

  // Enhanced marker icon with search highlighting
  const createSearchHighlightIcon = (income, isHighlighted = false) => {
    const baseColor = income > 4000 ? '#10b981' : income > 2000 ? '#f59e0b' : '#ef4444';
    const color = isHighlighted ? '#8b5cf6' : baseColor; // Purple when highlighted
    const size = isHighlighted ? 35 : 25; // Larger when highlighted
    
    return L.divIcon({
      html: `
        <div style="
          background-color: ${color};
          border: ${isHighlighted ? '3px solid #ffffff' : '2px solid white'};
          border-radius: 50%;
          width: ${size}px;
          height: ${size}px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: ${isHighlighted ? '12px' : '10px'};
          font-weight: bold;
          color: white;
          box-shadow: 0 ${isHighlighted ? '4px 8px' : '2px 4px'} rgba(0,0,0,0.3);
          ${isHighlighted ? 'animation: pulse 2s infinite;' : ''}
          z-index: ${isHighlighted ? '1000' : 'auto'};
        ">
          ${isHighlighted ? '📍' : `£${Math.round(income / 1000)}k`}
        </div>
        ${isHighlighted ? `
          <style>
            @keyframes pulse {
              0% { transform: scale(1); }
              50% { transform: scale(1.1); }
              100% { transform: scale(1); }
            }
          </style>
        ` : ''}
      `,
      className: 'custom-marker',
      iconSize: [size, size],
      iconAnchor: [size/2, size/2],
    });
  };

  const mapTownToBackendCity = (town) => {
    // Temporary mapping until backend is updated
    const townMapping = {
      // Vale of White Horse towns -> use existing vale_of_white_horse endpoint (if available)
      'vale_abingdon': 'vale_of_white_horse',
      'vale_botley': 'vale_of_white_horse', 
      'vale_kennington': 'vale_of_white_horse',
      'vale_wantage': 'vale_of_white_horse',
      'vale_other': 'vale_of_white_horse',
      
      // South Oxfordshire towns -> use existing south_oxfordshire endpoint (if available)
      'south_didcot': 'south_oxfordshire',
      'south_henley': 'south_oxfordshire',      // This fixes the immediate issue
      'south_thame': 'south_oxfordshire',
      'south_wallingford': 'south_oxfordshire',
      'south_other': 'south_oxfordshire'
    };
    
    return townMapping[town] || town;
  };

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
      // Use the mapped backend city
      const backendCity = mapTownToBackendCity(city);
      const response = await fetch(`http://localhost:8001/api/hmo-registry/cities/${backendCity}?enable_geocoding=true`);
      console.log(`🔘 ${city} Response status:`, response.status);
      
      const result = await response.json();
      console.log(`🔘 ${city} Response data:`, result);
      
      if (result.success) {
        console.log(`✅ Loaded ${result.data.length} ${city} HMO properties`);

        setHmoData(prev => ({
          ...prev,
          [city]: result.data  // Store under the original city key
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

  // Calculate map center with search integration
  const calculateMapCenter = useMemo(() => {
    // If we have a search-selected center, use that
    if (mapCenter && mapCenter[0] !== 51.7520 && mapCenter[1] !== -1.2577) {
      return mapCenter;
    }
    
    // Otherwise calculate from filtered properties
    if (filteredProperties.length === 0) return [51.7520, -1.2577]; // Oxford center
    
    const avgLat = filteredProperties.reduce((sum, p) => sum + p.latitude, 0) / filteredProperties.length;
    const avgLng = filteredProperties.reduce((sum, p) => sum + p.longitude, 0) / filteredProperties.length;
    
    return [avgLat, avgLng];
  }, [filteredProperties, mapCenter]);

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
      height: '100vh', 
      width: `calc(100vw - ${sidebarCollapsed ? '80px' : '280px'})`, // KEY FIX 
      position: 'fixed',
      top: 0,
      left: sidebarCollapsed ? '80px' : '280px', // KEY FIX
      margin: 0, 
      padding: 0,
      zIndex: 10,
      transition: 'left 0.3s ease, width 0.3s ease' // SMOOTH TRANSITION
    }}>
      {/* Sidebar with filters */}
      {/* ENHANCED FILTERS SIDEBAR - matching main sidebar styling */}
      <div style={{ 
        position: 'absolute',
        top: 0,
        left: sidebarOpen ? '0' : '-400px',
        width: '380px',
        height: '100%',
        background: isDarkMode ? theme.cardBg : baseColors.lightCream,
        borderRight: `1px solid ${isDarkMode ? theme.border : 'rgba(44, 62, 74, 0.1)'}`,
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
        zIndex: 1000,
        transition: 'left 0.3s ease',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* Header matching main sidebar */}
        <div style={{
          padding: '1.5rem',
          borderBottom: `1px solid ${isDarkMode ? theme.border : 'rgba(44, 62, 74, 0.1)'}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          backgroundColor: isDarkMode ? 'rgba(0, 0, 0, 0.05)' : 'rgba(255, 255, 255, 0.6)'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}>
            <div style={{
              width: '28px',
              height: '28px',
              background: theme.accent,
              borderRadius: '6px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Filter size={14} style={{ color: 'white' }} />
            </div>
            <span style={{ 
              fontSize: '1.1rem',
              fontWeight: '600',
              color: isDarkMode ? theme.text : baseColors.darkSlate
            }}>
              Map Filters
            </span>
          </div>
          
          <button
            onClick={() => setSidebarOpen(false)}
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '6px',
              backgroundColor: isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(44, 62, 74, 0.1)',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.2s ease'
            }}
          >
            <X size={14} style={{ color: isDarkMode ? theme.text : baseColors.darkSlate }} />
          </button>
        </div>

        {/* Filter Content */}
        <div style={{
          flex: 1,
          padding: '1.5rem',
          overflowY: 'auto'
        }}>
        
        {/* Property Count */}
        <div style={{ 
          marginBottom: '1.5rem', 
          padding: '1rem', 
          backgroundColor: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(255, 255, 255, 0.7)',
          borderRadius: '8px',
          border: `1px solid ${isDarkMode ? theme.border : 'rgba(44, 62, 74, 0.1)'}`
        }}>
          <div style={{ 
            fontSize: '0.875rem', 
            color: isDarkMode ? theme.textSecondary : baseColors.softGray,
            marginBottom: '0.25rem'
          }}>
            Showing Properties
          </div>
          <div style={{ 
            fontSize: '1.25rem',
            fontWeight: '600',
            color: isDarkMode ? theme.text : baseColors.darkSlate
          }}>
            {filteredProperties.length} of {properties.length}
          </div>
        </div>

        {/* Property Filters Section */}
        <div style={{ marginBottom: '2rem' }}>
          <h3 style={{ 
            fontSize: '1rem', 
            fontWeight: '600', 
            marginBottom: '1rem', 
            color: isDarkMode ? theme.text : baseColors.darkSlate,
            letterSpacing: '-0.25px'
          }}>
            Property Filters
          </h3>
                  
          {/* Income Filter */}
          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ 
              display: 'block', 
              fontSize: '0.875rem', 
              fontWeight: '500', 
              marginBottom: '0.75rem', 
              color: isDarkMode ? theme.textSecondary : baseColors.softGray
            }}>
              Min Monthly Income: £{filters.minIncome.toLocaleString()}
            </label>
            <input
              type="range"
              min="0"
              max="6000"
              step="100"
              value={filters.minIncome}
              onChange={(e) => setFilters(prev => ({ ...prev, minIncome: parseInt(e.target.value) }))}
              style={{ 
                width: '100%', 
                height: '4px', 
                borderRadius: '2px',
                background: isDarkMode ? '#374151' : '#e5e7eb',
                outline: 'none',
                appearance: 'none'
              }}
            />
          </div>

          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ 
              display: 'block', 
              fontSize: '0.875rem', 
              fontWeight: '500', 
              marginBottom: '0.75rem', 
              color: isDarkMode ? theme.textSecondary : baseColors.softGray
            }}>
              Max Monthly Income: £{filters.maxIncome.toLocaleString()}
            </label>
            <input
              type="range"
              min="0"
              max="10000"
              step="100"
              value={filters.maxIncome}
              onChange={(e) => setFilters(prev => ({ ...prev, maxIncome: parseInt(e.target.value) }))}
              style={{ 
                width: '100%', 
                height: '4px', 
                borderRadius: '2px',
                background: isDarkMode ? '#374151' : '#e5e7eb',
                outline: 'none',
                appearance: 'none'
              }}
            />
          </div>

          {/* Bills Filter */}
          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ 
              display: 'block', 
              fontSize: '0.875rem', 
              fontWeight: '500', 
              marginBottom: '0.75rem', 
              color: isDarkMode ? theme.textSecondary : baseColors.softGray
            }}>
              Bills Included
            </label>
            <select
              value={filters.billsIncluded}
              onChange={(e) => setFilters(prev => ({ ...prev, billsIncluded: e.target.value }))}
              style={{ 
                width: '100%', 
                padding: '0.75rem', 
                border: `1px solid ${isDarkMode ? theme.border : 'rgba(44, 62, 74, 0.2)'}`,
                borderRadius: '6px',
                fontSize: '0.875rem',
                backgroundColor: isDarkMode ? theme.cardBg : '#ffffff',
                color: isDarkMode ? theme.text : baseColors.darkSlate,
                outline: 'none'
              }}
            >
              <option value="all">All Properties</option>
              <option value="yes">Bills Included</option>
              <option value="no">Bills Not Included</option>
            </select>
          </div>

          {/* Rooms Filter */}
          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ 
              display: 'block', 
              fontSize: '0.875rem', 
              fontWeight: '500', 
              marginBottom: '0.75rem', 
              color: isDarkMode ? theme.textSecondary : baseColors.softGray
            }}>
              Minimum Rooms: {filters.minRooms}
            </label>
            <input
              type="range"
              min="0"
              max="10"
              value={filters.minRooms}
              onChange={(e) => setFilters(prev => ({ ...prev, minRooms: parseInt(e.target.value) }))}
              style={{ 
                width: '100%', 
                height: '4px', 
                borderRadius: '2px',
                background: isDarkMode ? '#374151' : '#e5e7eb',
                outline: 'none',
                appearance: 'none'
              }}
            />
            
            <label style={{ 
              display: 'block', 
              fontSize: '0.875rem', 
              fontWeight: '500', 
              marginBottom: '0.75rem', 
              marginTop: '1rem', 
              color: isDarkMode ? theme.textSecondary : baseColors.softGray
            }}>
              Maximum Rooms: {filters.maxRooms}
            </label>
            <input
              type="range"
              min="0"
              max="20"
              value={filters.maxRooms}
              onChange={(e) => setFilters(prev => ({ ...prev, maxRooms: parseInt(e.target.value) }))}
              style={{ 
                width: '100%', 
                height: '4px', 
                borderRadius: '2px',
                background: isDarkMode ? '#374151' : '#e5e7eb',
                outline: 'none',
                appearance: 'none'
              }}
            />
          </div>

          {/* Reset Button */}
          <button
            onClick={() => setFilters({ minIncome: 0, maxIncome: 10000, billsIncluded: 'all', minRooms: 0, maxRooms: 20 })}
            style={{ 
              width: '100%', 
              padding: '0.75rem', 
              backgroundColor: isDarkMode ? '#4b5563' : baseColors.softGray,
              color: 'white',
              border: 'none', 
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '0.875rem',
              fontWeight: '500',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.target.style.backgroundColor = isDarkMode ? '#6b7280' : '#8b8b8b';
            }}
            onMouseLeave={(e) => {
              e.target.style.backgroundColor = isDarkMode ? '#4b5563' : baseColors.softGray;
            }}
          >
            Reset Filters
          </button>
        </div>

        {/* HMO Registry Section */}
        <div style={{ 
          marginBottom: '2rem', 
          padding: '1.25rem', 
          borderRadius: '8px', 
          backgroundColor: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(255, 255, 255, 0.7)',
          border: `1px solid ${isDarkMode ? theme.border : 'rgba(44, 62, 74, 0.1)'}`
        }}>
          <h3 style={{ 
            fontSize: '1rem', 
            fontWeight: '600', 
            marginBottom: '1rem', 
            color: isDarkMode ? theme.text : baseColors.darkSlate,
            letterSpacing: '-0.25px'
          }}>
            HMO Registry
          </h3>
          
          {/* Cities in clean format */}
          {Object.entries(cityConfig)
            .sort(([,a], [,b]) => a.name.localeCompare(b.name))
            .map(([cityKey, cityInfo]) => (
            <div key={cityKey} style={{ marginBottom: '1rem' }}>
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '0.75rem', 
                marginBottom: '0.5rem' 
              }}>
                <div style={{ 
                  width: '10px', 
                  height: '10px', 
                  backgroundColor: cityInfo.color, 
                  borderRadius: '50%' 
                }}></div>
                <span style={{ 
                  fontWeight: '500', 
                  color: isDarkMode ? theme.text : baseColors.darkSlate,
                  fontSize: '0.875rem'
                }}>
                  {cityInfo.name}
                </span>
              </div>
              
              <button
                onClick={() => fetchHMOData(cityKey)}
                disabled={hmoLoading[cityKey]}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  padding: '0.5rem 0.75rem',
                  backgroundColor: hmoVisible[cityKey] ? '#dc2626' : cityInfo.color,
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: hmoLoading[cityKey] ? 'not-allowed' : 'pointer',
                  fontSize: '0.75rem',
                  fontWeight: '500',
                  opacity: hmoLoading[cityKey] ? 0.6 : 1,
                  transition: 'all 0.2s ease'
                }}
              >
                {hmoLoading[cityKey] ? (
                  <>
                    <div style={{ 
                      width: '10px', 
                      height: '10px', 
                      border: '2px solid #ffffff', 
                      borderTop: '2px solid transparent', 
                      borderRadius: '50%', 
                      animation: 'spin 1s linear infinite' 
                    }}></div>
                    Loading...
                  </>
                ) : hmoVisible[cityKey] ? (
                  <>Hide {cityInfo.name} HMOs</>
                ) : (
                  <>Show {cityInfo.name} HMOs</>
                )}
              </button>

              {/* Statistics */}
              {hmoVisible[cityKey] && hmoStats[cityKey] && (
                <div style={{ 
                  fontSize: '0.75rem', 
                  color: isDarkMode ? theme.textSecondary : baseColors.softGray, 
                  marginTop: '0.5rem',
                  paddingLeft: '1.75rem'
                }}>
                  <div>
                    <strong>{hmoStats[cityKey].total_records?.toLocaleString()}</strong> total 
                    ({hmoStats[cityKey].geocoded_records?.toLocaleString()} on map)
                  </div>
                  <div>
                    <span style={{ color: '#16a34a' }}>
                      {hmoStats[cityKey].active_licences?.toLocaleString()} active
                    </span>, 
                    <span style={{ color: '#dc2626' }}>
                      {hmoStats[cityKey].expired_licences?.toLocaleString()} expired
                    </span>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Legend */}
        <div>
          <h3 style={{ 
            fontSize: '1rem', 
            fontWeight: '600', 
            marginBottom: '1rem', 
            color: isDarkMode ? theme.text : baseColors.darkSlate,
            letterSpacing: '-0.25px'
          }}>
            Property Income Legend
          </h3>
          <div style={{ fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{ 
                width: '12px', 
                height: '12px', 
                backgroundColor: '#10b981', 
                borderRadius: '50%',
                border: '2px solid white', 
                boxShadow: '0 1px 3px rgba(0,0,0,0.2)' 
              }}></div>
              <span style={{ color: isDarkMode ? theme.textSecondary : baseColors.softGray }}>
                High Income (£4k+)
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{ 
                width: '12px', 
                height: '12px', 
                backgroundColor: '#f59e0b', 
                borderRadius: '50%',
                border: '2px solid white', 
                boxShadow: '0 1px 3px rgba(0,0,0,0.2)' 
              }}></div>
              <span style={{ color: isDarkMode ? theme.textSecondary : baseColors.softGray }}>
                Medium Income (£2-4k)
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{ 
                width: '12px', 
                height: '12px', 
                backgroundColor: '#ef4444', 
                borderRadius: '50%',
                border: '2px solid white', 
                boxShadow: '0 1px 3px rgba(0,0,0,0.2)' 
              }}></div>
              <span style={{ color: isDarkMode ? theme.textSecondary : baseColors.softGray }}>
                Lower Income (&lt;£2k)
              </span>
            </div>
          </div>
        </div>
        </div>
      </div>

      {/* ENHANCED FILTERS TOGGLE BUTTON */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        style={{
          position: 'absolute',
          top: '7rem',
          left: sidebarOpen ? '400px' : '1.5rem',
          zIndex: 1001,
          background: theme.sidebarBg, // Same gradient as sidebars
          border: `1px solid ${theme.border}`,
          borderRadius: '12px',
          padding: '0.875rem 1.25rem',
          cursor: 'pointer',
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.15)',
          fontSize: '0.875rem',
          fontWeight: '600',
          color: 'rgba(255, 255, 255, 0.9)',
          transition: 'all 0.3s ease',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          backdropFilter: 'blur(8px)',
          WebkitBackdropFilter: 'blur(8px)'
        }}
        onMouseEnter={(e) => {
          e.target.style.transform = 'translateY(-2px)';
          e.target.style.boxShadow = '0 6px 20px rgba(0, 0, 0, 0.2)';
        }}
        onMouseLeave={(e) => {
          e.target.style.transform = 'translateY(0)';
          e.target.style.boxShadow = '0 4px 16px rgba(0, 0, 0, 0.15)';
        }}
      >
        <Filter size={16} />
        {sidebarOpen ? 'Hide Filters' : 'Show Filters'}
        {!sidebarOpen && (
          <span style={{
            backgroundColor: 'rgba(255, 255, 255, 0.2)',
            borderRadius: '8px',
            padding: '0.125rem 0.5rem',
            fontSize: '0.75rem',
            fontWeight: '500'
          }}>
            {filteredProperties.length}
          </span>
        )}
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
      <div style={{ 
        height: 'calc(100% - 4rem)', // Reserve space at the top for controls
        width: '100%', 
        position: 'relative',
        marginTop: '5rem' // Push the map down to make room for controls
      }}>
        {/* Overlay Search Component */}
        <div style={{
          position: 'absolute',
          top: '1.5rem',
          right: '1.5rem',
          zIndex: 1002,
          width: '400px',
          maxWidth: '90vw'
        }}>
          <div style={{
            background: isDarkMode 
              ? 'rgba(44, 62, 74, 0.85)' 
              : 'rgba(255, 255, 255, 0.85)',
            backdropFilter: 'blur(12px)',
            WebkitBackdropFilter: 'blur(12px)',
            borderRadius: '16px',
            border: `1px solid ${theme.border}`,
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.15)',
            padding: '1rem',
            transition: 'all 0.3s ease'
          }}>
            <MapSearch
              properties={filteredProperties}
              hmoData={hmoData}
              cityConfig={cityConfig}
              onResultSelect={handleSearchResultSelect}
              onMapCenter={handleMapCenter}
              isOverlay={true}
              isDarkMode={isDarkMode}
              theme={theme}
            />
          </div>
        </div>
        <MapContainer
          center={calculateMapCenter}
          zoom={mapZoom}
          style={{ height: '100%', width: '100%' }}
          zoomControl={false}
          key={`${calculateMapCenter[0]}-${calculateMapCenter[1]}-${mapZoom}`}
        >
          <MapRefHandler onMapReady={handleMapCreated} />
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          
          {/* Render tracked property markers with search highlighting */}
          {filteredProperties.map((property) => {
            const isSearchHighlighted = searchSelectedMarker?.type === 'tracked_property' && 
                                      searchSelectedMarker?.data?.property_id === property.property_id;
            
            return (
              <Marker
                key={property.property_id}
                position={[property.latitude, property.longitude]}
                icon={createSearchHighlightIcon(property.monthly_income || 0, isSearchHighlighted)}
                zIndexOffset={isSearchHighlighted ? 2000 : 1000}
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
            );
          })}

          {/* Search-selected HMO marker */}
          {searchSelectedMarker?.type === 'hmo_property' && searchSelectedMarker.coordinates && (
            <Marker
              position={searchSelectedMarker.coordinates}
              icon={L.divIcon({
                html: `
                  <div style="
                    background-color: #8b5cf6;
                    border: 3px solid #ffffff;
                    border-radius: 50%;
                    width: 25px;
                    height: 25px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 14px;
                    color: white;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                    animation: pulse 2s infinite;
                    z-index: 1000;
                  ">
                    🏛️
                  </div>
                  <style>
                    @keyframes pulse {
                      0% { transform: scale(1); }
                      50% { transform: scale(1.2); }
                      100% { transform: scale(1); }
                    }
                  </style>
                `,
                className: 'search-selected-hmo-marker',
                iconSize: [25, 25],
                iconAnchor: [12, 12],
              })}
              zIndexOffset={2000}
            >
              <Popup>
                <div style={{ padding: '0.5rem' }}>
                  <h3 style={{ fontSize: '1rem', fontWeight: 'bold', marginBottom: '0.75rem', color: '#1f2937' }}>
                    🏛️ {searchSelectedMarker.title}
                  </h3>
                  <div style={{ fontSize: '0.875rem' }}>
                    <div><strong>City:</strong> {cityConfig[searchSelectedMarker.cityKey]?.name}</div>
                    <div><strong>License Status:</strong> {searchSelectedMarker.data.licence_status}</div>
                    {searchSelectedMarker.data.licensee && (
                      <div><strong>Licensee:</strong> {searchSelectedMarker.data.licensee}</div>
                    )}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '0.5rem' }}>
                    Found via search • HMO Registry
                  </div>
                </div>
              </Popup>
            </Marker>
          )}

          {/* Search-selected geocoded address marker */}
          {searchSelectedMarker?.type === 'geocoded_address' && searchSelectedMarker.coordinates && (
            <Marker
              position={searchSelectedMarker.coordinates}
              icon={L.divIcon({
                html: `
                  <div style="
                    background-color: #f59e0b;
                    border: 3px solid #ffffff;
                    border-radius: 50%;
                    width: 25px;
                    height: 25px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 14px;
                    color: white;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                    animation: pulse 2s infinite;
                  ">
                    📍
                  </div>
                `,
                className: 'search-selected-geocoded-marker',
                iconSize: [25, 25],
                iconAnchor: [12, 12],
              })}
              zIndexOffset={2000}
            >
              <Popup>
                <div style={{ padding: '0.5rem' }}>
                  <h3 style={{ fontSize: '1rem', fontWeight: 'bold', marginBottom: '0.75rem', color: '#1f2937' }}>
                    📍 {searchSelectedMarker.title}
                  </h3>
                  <div style={{ fontSize: '0.875rem' }}>
                    <div><strong>Address:</strong> {searchSelectedMarker.address}</div>
                    {searchSelectedMarker.postcode && (
                      <div><strong>Postcode:</strong> {searchSelectedMarker.postcode}</div>
                    )}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '0.5rem' }}>
                    Found via geocoding • Not in database
                  </div>
                  <div style={{ marginTop: '10px' }}>
                    <button
                      onClick={() => {
                        const url = `https://www.spareroom.co.uk/flatshare/?search_id=1234&mode=list&region=&flatshare_type=offered&location_type=area&location=${encodeURIComponent(searchSelectedMarker.address)}`;
                        window.open(url, '_blank');
                      }}
                      style={{
                        padding: '6px 12px',
                        backgroundColor: '#f59e0b',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '12px'
                      }}
                    >
                      Search SpareRoom
                    </button>
                  </div>
                </div>
              </Popup>
            </Marker>
          )}
        </MapContainer>
      </div>

      {/* Search Result Info Panel */}
      {searchSelectedMarker && (
        <div style={{
          position: 'absolute',
          bottom: '20px',
          left: '50%',
          transform: 'translateX(-50%)',
          backgroundColor: 'white',
          padding: '16px',
          borderRadius: '12px',
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
          border: '2px solid #8b5cf6',
          zIndex: 1000,
          maxWidth: '400px',
          minWidth: '300px'
        }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
            <div style={{ fontSize: '24px', flexShrink: 0 }}>
              {searchSelectedMarker.icon}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <h4 style={{ 
                margin: '0 0 4px 0', 
                fontSize: '16px', 
                fontWeight: '600',
                color: '#1f2937',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap'
              }}>
                {searchSelectedMarker.title}
              </h4>
              <p style={{ 
                margin: '0 0 8px 0', 
                fontSize: '14px', 
                color: '#6b7280',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap'
              }}>
                {searchSelectedMarker.subtitle}
              </p>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '12px'
              }}>
                <span style={{
                  backgroundColor: searchSelectedMarker.color,
                  color: 'white',
                  padding: '2px 8px',
                  borderRadius: '12px',
                  fontWeight: '600',
                  textTransform: 'uppercase'
                }}>
                  {searchSelectedMarker.type === 'tracked_property' ? 'TRACKED' :
                   searchSelectedMarker.type === 'hmo_property' ? 'HMO REGISTRY' : 'EXTERNAL'}
                </span>
                <span style={{ color: '#9ca3af' }}>
                  • Selected from search
                </span>
              </div>
            </div>
            <button
              onClick={() => setSearchSelectedMarker(null)}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                fontSize: '18px',
                color: '#9ca3af',
                padding: '4px',
                borderRadius: '4px',
                flexShrink: 0
              }}
              onMouseEnter={(e) => {
                e.target.style.backgroundColor = '#f3f4f6';
                e.target.style.color = '#374151';
              }}
              onMouseLeave={(e) => {
                e.target.style.backgroundColor = 'transparent';
                e.target.style.color = '#9ca3af';
              }}
            >
              ✕
            </button>
          </div>
        </div>
      )}

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

export default Map;