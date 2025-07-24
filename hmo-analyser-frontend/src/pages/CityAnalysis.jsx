import React, { useState, useEffect } from 'react';
import { TrendingUp, MapPin } from 'lucide-react';

const CitySelectionPage = () => {
  const [availableCities, setAvailableCities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchCitiesData = async () => {
      try {
        console.log('🏙️ Loading cities for selection...');
        
        // Get list of cities
        const citiesResponse = await fetch('/api/filters/cities');
        const citiesData = await citiesResponse.json();
        
        if (!citiesData.cities || citiesData.cities.length === 0) {
          console.log('❌ No cities found');
          setAvailableCities([]);
          setLoading(false);
          return;
        }

        // Get ALL properties in one request
        const allPropertiesResponse = await fetch('/api/properties?limit=10000');
        const allPropertiesData = await allPropertiesResponse.json();
        
        let allProperties;
        if (Array.isArray(allPropertiesData)) {
          allProperties = allPropertiesData;
        } else if (allPropertiesData.properties) {
          allProperties = allPropertiesData.properties;
        } else {
          allProperties = [];
        }

        console.log(`📊 Processing ${allProperties.length} total properties...`);

        // Group properties by city (extract from address)
        const extractCityFromAddress = (address) => {
          if (!address) return null;
          const addressParts = address.split(',').map(part => part.trim());
          
          for (const part of addressParts) {
            for (const cityName of citiesData.cities) {
              if (part.toLowerCase() === cityName.toLowerCase()) {
                return cityName;
              }
            }
          }
          return null;
        };
        
        const propertiesByCity = {};
        allProperties.forEach(property => {
          const cityValue = extractCityFromAddress(property.address);
          if (cityValue) {
            if (!propertiesByCity[cityValue]) {
              propertiesByCity[cityValue] = [];
            }
            propertiesByCity[cityValue].push(property);
          }
        });

        // Calculate metrics for each city
        const cityResults = [];
        for (const cityName of citiesData.cities) {
          const properties = propertiesByCity[cityName] || [];
          
          if (properties.length === 0) continue;

          let totalIncome = 0;
          let propertiesWithIncome = 0;
          
          properties.forEach(property => {
            if (property.monthly_income && property.monthly_income > 0) {
              totalIncome += property.monthly_income;
              propertiesWithIncome++;
            }
          });
          
          const avgIncome = propertiesWithIncome > 0 ? Math.round(totalIncome / propertiesWithIncome) : 0;
          
          cityResults.push({
            name: cityName,
            propertyCount: properties.length,
            avgIncome,
            totalIncome: Math.round(totalIncome),
            propertiesWithIncome
          });
        }

        // Sort by property count (most properties first)
        cityResults.sort((a, b) => b.propertyCount - a.propertyCount);
        
        console.log(`✅ Found ${cityResults.length} cities with properties`);
        setAvailableCities(cityResults);
        setLoading(false);
        
      } catch (error) {
        console.error('❌ Error fetching cities:', error);
        setError(`Failed to load cities: ${error.message}`);
        setLoading(false);
      }
    };

    fetchCitiesData();
  }, []);

  const handleCitySelect = (city) => {
    // Navigate to individual city analysis page
    const cityUrl = city.name.toLowerCase().replace(/\s+/g, '-');
    window.location.href = `/cityanalysis/${cityUrl}`;
  };

  if (loading) {
    return (
      <div style={{
        minHeight: '100vh',
        backgroundColor: '#f9fafb',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: '48px',
            height: '48px',
            border: '2px solid #e5e7eb',
            borderTop: '2px solid #2563eb',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 16px'
          }}></div>
          <p style={{ color: '#6b7280' }}>Loading cities...</p>
        </div>
        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#f9fafb',
      padding: '32px 0'
    }}>
      <div style={{
        maxWidth: '1152px',
        margin: '0 auto',
        padding: '0 16px'
      }}>
        <div style={{
          textAlign: 'center',
          marginBottom: '32px'
        }}>
          <h1 style={{
            fontSize: '2rem',
            fontWeight: 'bold',
            color: '#111827',
            marginBottom: '8px'
          }}>
            City Analysis
          </h1>
          <p style={{ color: '#6b7280' }}>
            Select a city to view detailed market analysis and insights
          </p>
        </div>

        {/* Error State */}
        {error && (
          <div style={{
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '8px',
            padding: '16px',
            marginBottom: '24px',
            textAlign: 'center'
          }}>
            <p style={{ color: '#dc2626', marginBottom: '8px' }}>⚠️ {error}</p>
            <button
              onClick={() => window.location.reload()}
              style={{
                backgroundColor: '#dc2626',
                color: 'white',
                border: 'none',
                padding: '8px 16px',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              Refresh Page
            </button>
          </div>
        )}

        {/* Empty State */}
        {!error && availableCities.length === 0 && (
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '48px',
            textAlign: 'center',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
          }}>
            <MapPin style={{
              width: '48px',
              height: '48px',
              color: '#d1d5db',
              margin: '0 auto 16px'
            }} />
            <h3 style={{
              fontSize: '1.25rem',
              fontWeight: '600',
              color: '#111827',
              marginBottom: '8px'
            }}>
              No Cities Available
            </h3>
            <p style={{ color: '#6b7280', marginBottom: '16px' }}>
              No cities with properties were found in your database.
            </p>
            <p style={{ color: '#6b7280', fontSize: '14px' }}>
              Try adding some properties first, then return to this page.
            </p>
          </div>
        )}

        {/* Cities Grid */}
        {!error && availableCities.length > 0 && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '24px'
          }}>
            {availableCities.map((city) => (
              <CityCard 
                key={city.name}
                city={city}
                onClick={() => handleCitySelect(city)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// City Card Component
const CityCard = ({ city, onClick }) => {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        boxShadow: isHovered ? '0 10px 15px -3px rgba(0, 0, 0, 0.1)' : '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        transition: 'all 0.2s',
        cursor: 'pointer',
        border: isHovered ? '1px solid #93c5fd' : '1px solid #e5e7eb',
        padding: '24px'
      }}
    >
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '16px'
      }}>
        <h3 style={{
          fontSize: '1.25rem',
          fontWeight: '600',
          color: isHovered ? '#2563eb' : '#111827',
          transition: 'color 0.2s'
        }}>
          {city.name}
        </h3>
        <MapPin style={{
          width: '20px',
          height: '20px',
          color: isHovered ? '#3b82f6' : '#9ca3af',
          transition: 'color 0.2s'
        }} />
      </div>
      
      <div style={{ marginBottom: '16px' }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: '14px',
          marginBottom: '8px'
        }}>
          <span style={{ color: '#6b7280' }}>Properties:</span>
          <span style={{ fontWeight: '500', color: '#111827' }}>{city.propertyCount}</span>
        </div>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: '14px',
          marginBottom: '8px'
        }}>
          <span style={{ color: '#6b7280' }}>Avg Income:</span>
          <span style={{ fontWeight: '500', color: '#059669' }}>£{city.avgIncome.toLocaleString()}/mo</span>
        </div>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: '14px'
        }}>
          <span style={{ color: '#6b7280' }}>Total Income:</span>
          <span style={{ fontWeight: '500', color: '#059669' }}>£{city.totalIncome.toLocaleString()}/mo</span>
        </div>
      </div>
      
      <div style={{
        display: 'flex',
        alignItems: 'center',
        color: isHovered ? '#1d4ed8' : '#2563eb',
        fontSize: '14px',
        fontWeight: '500',
        transition: 'color 0.2s'
      }}>
        View Analysis
        <TrendingUp style={{ width: '16px', height: '16px', marginLeft: '4px' }} />
      </div>
    </div>
  );
};

export default CitySelectionPage;