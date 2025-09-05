// src/components/Map.jsx - Replace your existing Map.jsx with this
import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { propertyApi } from '../utils/api';
import L from 'leaflet';

// Fix Leaflet default markers - CRITICAL for markers to show
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

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

const Map = ({ properties = [], usageTracker }) => {
  const navigate = useNavigate();
  const [selectedProperty, setSelectedProperty] = useState(null);
  const [filters, setFilters] = useState({
    minIncome: 0,
    maxIncome: 10000,
    billsIncluded: 'all',
    minRooms: 0
  });

  console.log('🗺️ Map received', properties.length, 'properties as props');

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
      if (rooms < filters.minRooms) return false;
      
      return true;
    });
  }, [properties, filters]);

  // Calculate map center based on properties
  const mapCenter = useMemo(() => {
    if (filteredProperties.length === 0) return [54.5, -2.0]; // UK center
    
    const avgLat = filteredProperties.reduce((sum, p) => sum + p.latitude, 0) / filteredProperties.length;
    const avgLng = filteredProperties.reduce((sum, p) => sum + p.longitude, 0) / filteredProperties.length;
    
    return [avgLat, avgLng];
  }, [filteredProperties]);

  // If no properties provided, show a message
  if (!properties || properties.length === 0) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>📊</div>
          <div>No properties available for map display</div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ height: '100vh', width: '100%', display: 'flex' }}>
      {/* Sidebar with filters */}
      <div style={{ 
        width: '320px', 
        backgroundColor: 'white', 
        padding: '1rem', 
        borderRight: '1px solid #e5e7eb',
        overflowY: 'auto',
        boxShadow: '2px 0 4px rgba(0,0,0,0.1)'
      }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1rem', color: '#1f2937' }}>
          🏠 Property Map
        </h2>
        
        <div style={{ marginBottom: '1.5rem', padding: '0.75rem', backgroundColor: '#f3f4f6', borderRadius: '8px' }}>
          <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
            Showing <strong>{filteredProperties.length}</strong> of <strong>{properties.length}</strong> properties
          </div>
        </div>

        {/* Filters Section */}
        <div style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '0.75rem', color: '#374151' }}>
            🔍 Filters
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
          </div>

          {/* Reset Button */}
          <button
            onClick={() => setFilters({ minIncome: 0, maxIncome: 10000, billsIncluded: 'all', minRooms: 0 })}
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

        {/* Legend */}
        <div style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: '600', marginBottom: '0.75rem', color: '#374151' }}>
            📊 Income Legend
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

      {/* Map Container */}
      <div style={{ flex: 1 }}>
        <MapContainer
          center={mapCenter}
          zoom={filteredProperties.length > 0 ? 8 : 6}
          style={{ height: '100%', width: '100%' }}
          zoomControl={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          
          {filteredProperties.map((property) => (
            <Marker
              key={property.property_id}
              position={[property.latitude, property.longitude]}
              icon={createMarkerIcon(property.monthly_income || 0)}
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
    </div>
  );
};

export default Map;