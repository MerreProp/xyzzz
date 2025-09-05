//Create new file: src/components/MapSearch.jsx

import React, { useState, useEffect, useRef } from 'react';
import { debounce } from 'lodash';

const MapSearch = ({ 
  properties = [], 
  hmoData = {}, 
  onResultSelect, 
  onMapCenter,
  cityConfig = {},
  isOverlay = false, // New prop to determine if it's an overlay
  isDarkMode = false,
  theme = {}
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [isExpanded, setIsExpanded] = useState(!isOverlay); // Collapsed by default on mobile overlay
  const searchInputRef = useRef(null);
  const resultsRef = useRef(null);

  // Debounced search function
  const debouncedSearch = useRef(
    debounce(async (query) => {
      if (!query || query.length < 2) {
        setSearchResults([]);
        setShowResults(false);
        return;
      }

      setIsSearching(true);
      const results = await performSearch(query);
      setSearchResults(results);
      setShowResults(results.length > 0);
      setSelectedIndex(-1);
      setIsSearching(false);
    }, 300)
  ).current;

  useEffect(() => {
    debouncedSearch(searchQuery);
  }, [searchQuery, debouncedSearch]);

  // Main search function with prioritization
  const performSearch = async (query) => {
    const results = [];
    const queryLower = query.toLowerCase();

    // Helper function to normalize text for searching
    const normalizeForSearch = (text) => {
      if (!text) return '';
      return text
        .toLowerCase()
        .replace(/[^\w\s]/g, ' ')  // Replace punctuation with spaces
        .replace(/\s+/g, ' ')      // Replace multiple spaces with single space
        .trim();
    };

    const normalizedQuery = normalizeForSearch(query);
    // 1. Search tracked properties (your analyzed properties) - TOP PRIORITY
    const trackedMatches = properties
      .filter(property => {
        if (!property.address) return false;
        const normalizedAddress = normalizeForSearch(property.address);
        const normalizedPostcode = normalizeForSearch(property.postcode);
        const normalizedAdvertiser = normalizeForSearch(property.advertiser_name);
        
        return normalizedAddress.includes(normalizedQuery) ||
              normalizedPostcode.includes(normalizedQuery) ||
              normalizedAdvertiser.includes(normalizedQuery);
      })
      .slice(0, 3) // Limit to 3 results
      .map(property => ({
        id: `tracked_${property.property_id}`,
        type: 'tracked_property',
        title: property.address,
        subtitle: `£${property.monthly_income?.toLocaleString() || 0}/month • ${property.total_rooms || 0} rooms`,
        address: property.address,
        postcode: property.postcode,
        coordinates: [property.latitude, property.longitude],
        data: property,
        icon: '🏠',
        color: '#10b981'
      }));

    results.push(...trackedMatches);

    // 2. Search HMO registry properties from all cities - SECOND PRIORITY
    Object.entries(hmoData).forEach(([cityKey, cityProperties]) => {
      if (!cityProperties || !Array.isArray(cityProperties)) return;

      const hmoMatches = cityProperties
        .filter(property => {
          if (!property.address) return false;
          const normalizedAddress = normalizeForSearch(property.address);
          const normalizedPostcode = normalizeForSearch(property.postcode);
          const normalizedLicensee = normalizeForSearch(property.licensee);
          const normalizedCaseNumber = normalizeForSearch(property.case_number);
          
          return normalizedAddress.includes(normalizedQuery) ||
                normalizedPostcode.includes(normalizedQuery) ||
                normalizedLicensee.includes(normalizedQuery) ||
                normalizedCaseNumber.includes(normalizedQuery);
        })
        .slice(0, 2) // Limit per city
        .map(property => ({
          id: `hmo_${cityKey}_${property.case_number || property.id}`,
          type: 'hmo_property',
          title: property.address,
          subtitle: `${cityConfig[cityKey]?.name || cityKey} • License: ${property.licence_status || 'Unknown'}`,
          address: property.address,
          postcode: property.postcode,
          coordinates: [property.latitude, property.longitude],
          data: property,
          cityKey,
          icon: '🏛️',
          color: cityConfig[cityKey]?.color || '#6b7280'
        }));

      results.push(...hmoMatches);
    });

    // Limit HMO results to 3 total
    const hmoResults = results.filter(r => r.type === 'hmo_property').slice(0, 3);
    const nonHmoResults = results.filter(r => r.type !== 'hmo_property');
    results.length = 0;
    results.push(...nonHmoResults, ...hmoResults);

    // 3. If no local results and query looks like an address, search via geocoding - LOWEST PRIORITY
    if (results.length === 0 && query.length > 5) {
      try {
        const geocodeResults = await searchAddressGeocoding(query);
        results.push(...geocodeResults.slice(0, 2)); // Limit external results
      } catch (error) {
        console.error('Geocoding search failed:', error);
      }
    }

    // Sort results: tracked properties first, then HMO, then geocoded
    return results.sort((a, b) => {
      const typeOrder = { 'tracked_property': 0, 'hmo_property': 1, 'geocoded_address': 2 };
      return typeOrder[a.type] - typeOrder[b.type];
    });
  };

  // Geocoding search for addresses not in database
  const searchAddressGeocoding = async (query) => {
    try {
      const encodedQuery = encodeURIComponent(`${query}, UK`);
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?q=${encodedQuery}&format=json&limit=2&countrycodes=gb&addressdetails=1`
      );

      if (!response.ok) throw new Error('Geocoding request failed');

      const data = await response.json();
      
      return data.map((result, index) => ({
        id: `geocoded_${index}`,
        type: 'geocoded_address',
        title: result.display_name.split(',')[0],
        subtitle: `${result.display_name.split(',').slice(1, 3).join(', ')} • External address`,
        address: result.display_name,
        postcode: result.address?.postcode,
        coordinates: [parseFloat(result.lat), parseFloat(result.lon)],
        data: result,
        icon: '📍',
        color: '#6b7280'
      }));
    } catch (error) {
      console.error('Geocoding error:', error);
      return [];
    }
  };

  // Handle keyboard navigation
  const handleKeyDown = (e) => {
    if (!showResults || searchResults.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev < searchResults.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => prev > 0 ? prev - 1 : -1);
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < searchResults.length) {
          handleResultSelect(searchResults[selectedIndex]);
        }
        break;
      case 'Escape':
        setShowResults(false);
        setSelectedIndex(-1);
        searchInputRef.current?.blur();
        break;
    }
  };

  // Handle result selection
  const handleResultSelect = (result) => {
    setSearchQuery(result.title);
    setShowResults(false);
    setSelectedIndex(-1);

    // Center map on selected result
    if (onMapCenter && result.coordinates) {
      onMapCenter(result.coordinates, 16);
    }

    // Trigger result selection callback
    if (onResultSelect) {
      onResultSelect(result);
    }

    searchInputRef.current?.blur();
    
    // Collapse on mobile after selection
    if (isOverlay && window.innerWidth < 768) {
      setIsExpanded(false);
    }
  };

  // Clear search
  const clearSearch = () => {
    setSearchQuery('');
    setSearchResults([]);
    setShowResults(false);
    setSelectedIndex(-1);
    searchInputRef.current?.focus();
  };

  // Handle mobile expand/collapse
  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
    if (!isExpanded) {
      // Focus input when expanding
      setTimeout(() => searchInputRef.current?.focus(), 100);
    }
  };

  // Click outside to close results
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (resultsRef.current && !resultsRef.current.contains(event.target) &&
          searchInputRef.current && !searchInputRef.current.contains(event.target)) {
        setShowResults(false);
        setSelectedIndex(-1);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Overlay styles - Better positioned and sized
  const overlayContainerStyle = {
    position: 'absolute',
    top: '1rem',
    right: '15rem',
    zIndex: 1000,
    maxWidth: isExpanded ? '400px' : '80px',  // Reduced width to fit better
    width: isExpanded ? '400px' : '80px',     
    minWidth: isExpanded ? '400px' : '80px',  
    transition: 'all 0.3s ease-in-out'
  };

  // Sidebar styles (original)
  const sidebarContainerStyle = {
    position: 'relative',
    width: '100%',
    maxWidth: '500px',  // Bigger for sidebar too
    minWidth: '500px',  // Force minimum
    zIndex: 1000
  };

  // Mobile responsive check
  const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;

  // If it's an overlay and collapsed on mobile, show search icon
  if (isOverlay && !isExpanded && isMobile) {
    return (
      <div style={overlayContainerStyle}>
        <button
          onClick={toggleExpanded}
          style={{
            width: '80px',     // Much bigger mobile icon
            height: '80px',    // Much bigger mobile icon
            borderRadius: '40px',
            backgroundColor: 'white',
            border: '4px solid #e5e7eb',  // Thicker border
            boxShadow: '0 12px 24px rgba(0, 0, 0, 0.2)',  // Bigger shadow
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '32px',  // Much bigger icon
            color: '#6b7280',
            transition: 'all 0.2s ease'
          }}
          onMouseEnter={(e) => {
            e.target.style.backgroundColor = '#f9fafb';
            e.target.style.borderColor = '#3b82f6';
            e.target.style.transform = 'scale(1.05)';
          }}
          onMouseLeave={(e) => {
            e.target.style.backgroundColor = 'white';
            e.target.style.borderColor = '#e5e7eb';
            e.target.style.transform = 'scale(1)';
          }}
        >
          🔍
        </button>
      </div>
    );
  }

  return (
    <div style={isOverlay ? overlayContainerStyle : sidebarContainerStyle}>
      {/* Search Input Container */}
      <div style={{ position: 'relative' }}>
        {/* Collapse button for mobile overlay */}
        {isOverlay && isMobile && isExpanded && (
          <button
            onClick={toggleExpanded}
            style={{
              position: 'absolute',
              left: '-70px',
              top: '50%',
              transform: 'translateY(-50%)',
              width: '50px',
              height: '50px',
              borderRadius: '25px',
              backgroundColor: 'white',
              border: '3px solid #e5e7eb',
              boxShadow: '0 6px 12px rgba(0, 0, 0, 0.15)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '20px',
              color: '#6b7280'
            }}
          >
            ✕
          </button>
        )}

        <input
          ref={searchInputRef}
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={(e) => {
            e.target.style.borderColor = theme.accent || '#3b82f6';
            e.target.style.boxShadow = `0 8px 16px -4px rgba(0, 0, 0, 0.1), 0 0 0 3px rgba(${theme.accent?.slice(1).match(/.{2}/g)?.map(hex => parseInt(hex, 16)).join(', ') || '59, 130, 246'}, 0.1)`;
            if (searchResults.length > 0) setShowResults(true);
          }}
          onBlur={(e) => {
            e.target.style.borderColor = theme.border || '#d1d5db';
            e.target.style.boxShadow = '0 4px 8px 0 rgba(0, 0, 0, 0.1)';
          }}
          placeholder={isOverlay ? "Search properties, addresses..." : "Search properties, HMOs, addresses..."}
          style={{
            width: '100%',
            minWidth: isOverlay ? '300px' : '100%',
            padding: '12px 16px',
            paddingRight: searchQuery ? '50px' : '16px',
            fontSize: '14px',
            fontWeight: '500',
            border: `2px solid ${theme.border || '#d1d5db'}`,
            borderRadius: '12px', // Consistent with theme
            outline: 'none',
            backgroundColor: isDarkMode ? theme.cardBg || '#2c3e4a' : '#ffffff',
            color: isDarkMode ? theme.text || '#f9fafb' : '#1f2937',
            boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
            transition: 'all 0.2s ease-in-out',
            boxSizing: 'border-box',
            height: '44px'
          }}
        />

        {/* Loading spinner */}
        {isSearching && (
          <div
            style={{
              position: 'absolute',
              right: '18px',
              top: '50%',
              transform: 'translateY(-50%)',
              width: '20px',      // Smaller spinner
              height: '20px',     
              border: '2px solid #f3f4f6',  // Thinner border
              borderTop: '2px solid #3b82f6',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite'
            }}
          />
        )}

        {/* Clear button */}
        {searchQuery && !isSearching && (
          <button
            onClick={clearSearch}
            style={{
              position: 'absolute',
              right: '-200px', // temporary fix for the clear button
              top: '50%',
              transform: 'translateY(-50%)',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              fontSize: '18px',      // Smaller clear button
              color: '#6b7280',
              padding: '4px',        // Less padding
              borderRadius: '6px',   
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.target.style.backgroundColor = '#f3f4f6';
              e.target.style.color = '#374151';
              e.target.style.transform = 'translateY(-50%) scale(1.1)';
            }}
            onMouseLeave={(e) => {
              e.target.style.backgroundColor = 'transparent';
              e.target.style.color = '#6b7280';
              e.target.style.transform = 'translateY(-50%) scale(1)';
            }}
          >
            ✕
          </button>
        )}
      </div>

      {/* Search Results Dropdown */}
      {showResults && searchResults.length > 0 && (
        <div
          ref={resultsRef}
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            width: '100%',
            backgroundColor: isDarkMode ? theme.cardBg || '#2c3e4a' : '#ffffff',
            border: `2px solid ${theme.accent || '#3b82f6'}`,
            borderTop: 'none',
            borderBottomLeftRadius: '12px',
            borderBottomRightRadius: '12px',
            boxShadow: '0 10px 25px rgba(0, 0, 0, 0.15)',
            maxHeight: '400px',
            overflowY: 'auto',
            zIndex: 1001
          }}
        >
          {searchResults.map((result, index) => (
            <div
              key={result.id}
              onClick={() => handleResultSelect(result)}
              style={{
                padding: '12px 16px',
                cursor: 'pointer',
                borderBottom: index < searchResults.length - 1 ? `1px solid ${theme.border || '#f3f4f6'}` : 'none',
                backgroundColor: selectedIndex === index 
                  ? (isDarkMode ? 'rgba(59, 130, 246, 0.2)' : '#f0f9ff')
                  : 'transparent',
                transition: 'background-color 0.15s ease'
              }}
              onMouseEnter={(e) => {
                if (selectedIndex !== index) {
                  e.target.style.backgroundColor = isDarkMode ? 'rgba(255, 255, 255, 0.05)' : '#f9fafb';
                }
              }}
              onMouseLeave={(e) => {
                if (selectedIndex !== index) {
                  e.target.style.backgroundColor = 'transparent';
                }
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{ fontSize: '16px' }}>{result.icon}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ 
                    fontWeight: '600', 
                    color: isDarkMode ? theme.text || '#f9fafb' : '#1f2937',
                    fontSize: '14px',
                    marginBottom: '2px'
                  }}>
                    {result.title}
                  </div>
                  <div style={{ 
                    fontSize: '12px', 
                    color: isDarkMode ? theme.textSecondary || '#9ca3af' : '#6b7280'
                  }}>
                    {result.subtitle}
                  </div>
                </div>
                <div
                  style={{
                    fontSize: '10px',
                    fontWeight: '700',
                    color: 'white',
                    backgroundColor: result.type === 'tracked_property' ? '#10b981' : 
                                  result.type === 'hmo_property' ? '#3b82f6' : '#6b7280',
                    padding: '3px 6px',
                    borderRadius: '10px',
                    textTransform: 'uppercase'
                  }}
                >
                  {result.type === 'tracked_property' ? 'TRACKED' :
                  result.type === 'hmo_property' ? 'HMO' : 'EXTERNAL'}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* No Results Message */}
      {showResults && searchResults.length === 0 && searchQuery.length > 2 && !isSearching && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          width: '400px',
          backgroundColor: 'white',
          border: '3px solid #e5e7eb',
          borderTop: 'none',
          borderBottomLeftRadius: '16px',
          borderBottomRightRadius: '16px',
          padding: '24px',
          textAlign: 'center',
          color: '#6b7280',
          fontSize: '16px'
        }}>
          <div style={{ fontSize: '32px', marginBottom: '12px' }}>🔍</div>
          <div style={{ fontWeight: '600', marginBottom: '8px' }}>No results found for "{searchQuery}"</div>
          <div style={{ fontSize: '14px' }}>
            Try searching for an address, postcode, or property name
          </div>
        </div>
      )}

      {/* Add CSS animation for spinner */}
      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>
    </div>
  );
};

export default MapSearch;