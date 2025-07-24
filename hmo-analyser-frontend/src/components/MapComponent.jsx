// Add this enhanced debugging to your MapComponent.jsx

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { propertyApi } from '../utils/api';
import Map from './Map'; // Make sure this import path is correct
import MapUsageTracker from '../utils/mapUsageTracker';
import MapUsageStats from './MapUsageStats';

// Create usage tracker instance
const mapUsageTracker = new MapUsageTracker();

const PropertyMapComponent = () => {
  // Fetch all properties using the same API call as other pages
  const { data: properties = [], isLoading, error, isSuccess } = useQuery({
    queryKey: ['properties'],
    queryFn: propertyApi.getAllProperties,
  });

  // Enhanced debugging
  console.log('🗺️ PropertyMapComponent Debug Info:');
  console.log('🗺️ isLoading:', isLoading);
  console.log('🗺️ isSuccess:', isSuccess);
  console.log('🗺️ error:', error);
  console.log('🗺️ Properties fetched:', properties?.length || 0);
  console.log('🗺️ Sample property:', properties?.[0]);
  console.log('🗺️ propertyApi object:', propertyApi);

  // Test if the API function exists
  if (!propertyApi.getAllProperties) {
    console.error('🚨 propertyApi.getAllProperties is not defined!');
  }

  if (isLoading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '50vh',
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
        <p style={{ color: '#9ca3af', fontSize: '0.875rem' }}>
          Debug: isLoading = {isLoading.toString()}
        </p>
      </div>
    );
  }

  if (error) {
    console.error('🚨 API Error details:', error);
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '50vh',
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

  // Show warning if no properties
  if (isSuccess && properties.length === 0) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '50vh',
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

  console.log('🗺️ About to render Map component with properties:', properties);

  return (
    <div style={{ position: 'relative', height: '100vh' }}>
      {/* Pass properties to the Map component */}
      <Map 
        properties={properties} 
        usageTracker={mapUsageTracker}
      />
      
      {/* Usage stats overlay */}
      <MapUsageStats tracker={mapUsageTracker} />
      
      {/* Add spin animation styles */}
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default PropertyMapComponent;