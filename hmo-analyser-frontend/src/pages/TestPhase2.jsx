import React, { useState, useEffect } from 'react';

const TestPhase2 = () => {
  const [testResults, setTestResults] = useState({
    databaseTables: null,
    apiEndpoints: null,
    priceTracking: null,
    trendsCalculation: null,
    sampleData: null
  });
  
  const [selectedProperty, setSelectedProperty] = useState(null);
  const [properties, setProperties] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch properties on component mount
  useEffect(() => {
    fetchProperties();
  }, []);

  const fetchProperties = async () => {
    try {
      const response = await fetch('/api/properties');
      const data = await response.json();
      setProperties(data.slice(0, 5)); // Get first 5 properties for testing
      if (data.length > 0) {
        setSelectedProperty(data[0].property_id);
      }
    } catch (error) {
      console.error('Failed to fetch properties:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Test 1: Database Tables
  const testDatabaseTables = async () => {
    try {
      setTestResults(prev => ({ ...prev, databaseTables: { status: 'testing' } }));
      
      // Test if Phase 2 tables exist by trying to query them
      const tests = [];
      
      // Test room_price_history table
      try {
        const response = await fetch('/api/test/price-history-table');
        tests.push({ table: 'room_price_history', exists: response.ok });
      } catch {
        tests.push({ table: 'room_price_history', exists: false });
      }
      
      // Test property_trends table
      try {
        const response = await fetch('/api/test/trends-table');
        tests.push({ table: 'property_trends', exists: response.ok });
      } catch {
        tests.push({ table: 'property_trends', exists: false });
      }
      
      const allTablesExist = tests.every(test => test.exists);
      
      setTestResults(prev => ({
        ...prev,
        databaseTables: {
          status: allTablesExist ? 'success' : 'error',
          message: allTablesExist ? 'All Phase 2 tables exist' : 'Some tables missing',
          details: tests
        }
      }));
    } catch (error) {
      setTestResults(prev => ({
        ...prev,
        databaseTables: {
          status: 'error',
          message: 'Failed to test database tables',
          error: error.message
        }
      }));
    }
  };

  // Test 2: API Endpoints
  const testApiEndpoints = async () => {
    if (!selectedProperty) return;
    
    try {
      setTestResults(prev => ({ ...prev, apiEndpoints: { status: 'testing' } }));
      
      const endpoints = [
        { name: 'Price Trends', url: `/api/properties/${selectedProperty}/price-trends` },
        { name: 'Property Analytics', url: `/api/properties/${selectedProperty}/analytics` },
        { name: 'Property Trends', url: `/api/properties/${selectedProperty}/trends` },
        { name: 'Timeline Data', url: `/api/properties/${selectedProperty}/availability-timeline` }
      ];
      
      const results = [];
      
      for (const endpoint of endpoints) {
        try {
          const response = await fetch(endpoint.url);
          const data = await response.json();
          results.push({
            name: endpoint.name,
            status: response.ok ? 'success' : 'error',
            statusCode: response.status,
            hasData: response.ok && data && Object.keys(data).length > 0
          });
        } catch (error) {
          results.push({
            name: endpoint.name,
            status: 'error',
            error: error.message
          });
        }
      }
      
      const allWorking = results.every(r => r.status === 'success');
      
      setTestResults(prev => ({
        ...prev,
        apiEndpoints: {
          status: allWorking ? 'success' : 'warning',
          message: allWorking ? 'All endpoints responding' : 'Some endpoints have issues',
          results
        }
      }));
    } catch (error) {
      setTestResults(prev => ({
        ...prev,
        apiEndpoints: {
          status: 'error',
          message: 'Failed to test API endpoints',
          error: error.message
        }
      }));
    }
  };

  // Test 3: Price Tracking
  const testPriceTracking = async () => {
    if (!selectedProperty) return;
    
    try {
      setTestResults(prev => ({ ...prev, priceTracking: { status: 'testing' } }));
      
      const response = await fetch(`/api/properties/${selectedProperty}/price-trends?days=365`);
      const data = await response.json();
      
      const hasChanges = data.total_changes > 0;
      const hasRoomData = Object.keys(data.changes_by_room || {}).length > 0;
      
      setTestResults(prev => ({
        ...prev,
        priceTracking: {
          status: response.ok ? 'success' : 'error',
          message: hasChanges ? 
            `Found ${data.total_changes} price changes` : 
            'No price changes recorded yet',
          details: {
            totalChanges: data.total_changes || 0,
            averageChange: data.average_change_amount || 0,
            trendDirection: data.trend_direction || 'stable',
            priceVolatility: data.price_volatility || 0,
            roomsWithChanges: Object.keys(data.changes_by_room || {}).length
          }
        }
      }));
    } catch (error) {
      setTestResults(prev => ({
        ...prev,
        priceTracking: {
          status: 'error',
          message: 'Failed to test price tracking',
          error: error.message
        }
      }));
    }
  };

  // Test 4: Trends Calculation
  const testTrendsCalculation = async () => {
    if (!selectedProperty) return;
    
    try {
      setTestResults(prev => ({ ...prev, trendsCalculation: { status: 'testing' } }));
      
      // Trigger trend calculation
      const calcResponse = await fetch(`/api/properties/${selectedProperty}/calculate-trends`, {
        method: 'POST'
      });
      
      if (calcResponse.ok) {
        // Get the calculated trends
        const trendsResponse = await fetch(`/api/properties/${selectedProperty}/trends`);
        const trendsData = await trendsResponse.json();
        
        setTestResults(prev => ({
          ...prev,
          trendsCalculation: {
            status: 'success',
            message: 'Trends calculated successfully',
            details: {
              trendsFound: trendsData.length,
              latestTrend: trendsData[0] || null
            }
          }
        }));
      } else {
        throw new Error(`Calculation failed: ${calcResponse.status}`);
      }
    } catch (error) {
      setTestResults(prev => ({
        ...prev,
        trendsCalculation: {
          status: 'error',
          message: 'Failed to calculate trends',
          error: error.message
        }
      }));
    }
  };

  // Test 5: Sample Data Generation
  const generateSampleData = async () => {
    if (!selectedProperty) return;
    
    try {
      setTestResults(prev => ({ ...prev, sampleData: { status: 'testing' } }));
      
      // This would create sample price changes for testing
      // In a real implementation, you'd trigger property re-analysis
      const response = await fetch(`/api/properties/${selectedProperty}/generate-sample-data`, {
        method: 'POST'
      });
      
      if (response.ok) {
        const data = await response.json();
        setTestResults(prev => ({
          ...prev,
          sampleData: {
            status: 'success',
            message: 'Sample data generated',
            details: data
          }
        }));
      } else {
        setTestResults(prev => ({
          ...prev,
          sampleData: {
            status: 'info',
            message: 'Sample data generation endpoint not implemented yet',
            note: 'This is normal - sample data generation is optional'
          }
        }));
      }
    } catch (error) {
      setTestResults(prev => ({
        ...prev,
        sampleData: {
          status: 'info',
          message: 'Sample data generation not available',
          note: 'This is normal - data will accumulate naturally over time'
        }
      }));
    }
  };

  // Run all tests
  const runAllTests = async () => {
    await testDatabaseTables();
    await testApiEndpoints();
    await testPriceTracking();
    await testTrendsCalculation();
    await generateSampleData();
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'success': return '✅';
      case 'warning': return '⚠️';
      case 'error': return '❌';
      case 'testing': return '🔄';
      case 'info': return 'ℹ️';
      default: return '⏳';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'success': return '#059669';
      case 'warning': return '#f59e0b';
      case 'error': return '#dc2626';
      case 'testing': return '#667eea';
      case 'info': return '#0ea5e9';
      default: return '#64748b';
    }
  };

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem' }}>
        <div className="spinner" style={{ width: '40px', height: '40px', margin: '0 auto 1rem' }}></div>
        <p>Loading Phase 2 test environment...</p>
      </div>
    );
  }

  return (
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '2rem' }}>
        🧪 Phase 2 Testing Dashboard
      </h1>

      {/* Property Selection */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <h3 className="card-title">🏠 Test Property Selection</h3>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <select
            value={selectedProperty || ''}
            onChange={(e) => setSelectedProperty(e.target.value)}
            style={{
              padding: '0.5rem',
              border: '1px solid #e5e7eb',
              borderRadius: '6px',
              fontSize: '0.875rem',
              minWidth: '300px'
            }}
          >
            {properties.map(property => (
              <option key={property.property_id} value={property.property_id}>
                {property.address || `Property ${property.property_id.slice(-8)}`}
              </option>
            ))}
          </select>
          
          <button
            onClick={runAllTests}
            className="btn btn-primary"
            disabled={!selectedProperty}
          >
            🧪 Run All Tests
          </button>
          
          {selectedProperty && (
            <a 
              href={`/property/${selectedProperty}`}
              className="btn btn-secondary"
              style={{ textDecoration: 'none' }}
            >
              📊 View Analytics
            </a>
          )}
        </div>
      </div>

      {/* Test Results */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '1.5rem' }}>
        
        {/* Database Tables Test */}
        <div className="card">
          <h3 className="card-title">
            {getStatusIcon(testResults.databaseTables?.status)} Database Tables
          </h3>
          <div style={{ marginBottom: '1rem' }}>
            <button onClick={testDatabaseTables} className="btn btn-secondary" style={{ fontSize: '0.875rem' }}>
              Test Tables
            </button>
          </div>
          {testResults.databaseTables && (
            <div>
              <div style={{ 
                color: getStatusColor(testResults.databaseTables.status),
                fontWeight: '500',
                marginBottom: '0.5rem'
              }}>
                {testResults.databaseTables.message}
              </div>
              {testResults.databaseTables.details && (
                <div style={{ fontSize: '0.875rem', color: '#64748b' }}>
                  {testResults.databaseTables.details.map(detail => (
                    <div key={detail.table}>
                      {detail.exists ? '✅' : '❌'} {detail.table}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* API Endpoints Test */}
        <div className="card">
          <h3 className="card-title">
            {getStatusIcon(testResults.apiEndpoints?.status)} API Endpoints
          </h3>
          <div style={{ marginBottom: '1rem' }}>
            <button 
              onClick={testApiEndpoints} 
              className="btn btn-secondary" 
              style={{ fontSize: '0.875rem' }}
              disabled={!selectedProperty}
            >
              Test Endpoints
            </button>
          </div>
          {testResults.apiEndpoints && (
            <div>
              <div style={{ 
                color: getStatusColor(testResults.apiEndpoints.status),
                fontWeight: '500',
                marginBottom: '0.5rem'
              }}>
                {testResults.apiEndpoints.message}
              </div>
              {testResults.apiEndpoints.results && (
                <div style={{ fontSize: '0.875rem' }}>
                  {testResults.apiEndpoints.results.map(result => (
                    <div key={result.name} style={{ marginBottom: '0.25rem' }}>
                      {result.status === 'success' ? '✅' : '❌'} {result.name}
                      {result.hasData && <span style={{ color: '#059669' }}> (has data)</span>}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Price Tracking Test */}
        <div className="card">
          <h3 className="card-title">
            {getStatusIcon(testResults.priceTracking?.status)} Price Tracking
          </h3>
          <div style={{ marginBottom: '1rem' }}>
            <button 
              onClick={testPriceTracking} 
              className="btn btn-secondary" 
              style={{ fontSize: '0.875rem' }}
              disabled={!selectedProperty}
            >
              Test Price History
            </button>
          </div>
          {testResults.priceTracking && (
            <div>
              <div style={{ 
                color: getStatusColor(testResults.priceTracking.status),
                fontWeight: '500',
                marginBottom: '0.5rem'
              }}>
                {testResults.priceTracking.message}
              </div>
              {testResults.priceTracking.details && (
                <div style={{ fontSize: '0.875rem', color: '#64748b' }}>
                  <div>Changes: {testResults.priceTracking.details.totalChanges}</div>
                  <div>Avg Change: £{testResults.priceTracking.details.averageChange}</div>
                  <div>Trend: {testResults.priceTracking.details.trendDirection}</div>
                  <div>Rooms: {testResults.priceTracking.details.roomsWithChanges}</div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Trends Calculation Test */}
        <div className="card">
          <h3 className="card-title">
            {getStatusIcon(testResults.trendsCalculation?.status)} Trends Calculation
          </h3>
          <div style={{ marginBottom: '1rem' }}>
            <button 
              onClick={testTrendsCalculation} 
              className="btn btn-secondary" 
              style={{ fontSize: '0.875rem' }}
              disabled={!selectedProperty}
            >
              Calculate Trends
            </button>
          </div>
          {testResults.trendsCalculation && (
            <div>
              <div style={{ 
                color: getStatusColor(testResults.trendsCalculation.status),
                fontWeight: '500',
                marginBottom: '0.5rem'
              }}>
                {testResults.trendsCalculation.message}
              </div>
              {testResults.trendsCalculation.details && (
                <div style={{ fontSize: '0.875rem', color: '#64748b' }}>
                  <div>Trends found: {testResults.trendsCalculation.details.trendsFound}</div>
                  {testResults.trendsCalculation.details.latestTrend && (
                    <div>Latest: {testResults.trendsCalculation.details.latestTrend.period_start}</div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Sample Data Test */}
        <div className="card">
          <h3 className="card-title">
            {getStatusIcon(testResults.sampleData?.status)} Sample Data
          </h3>
          <div style={{ marginBottom: '1rem' }}>
            <button 
              onClick={generateSampleData} 
              className="btn btn-secondary" 
              style={{ fontSize: '0.875rem' }}
              disabled={!selectedProperty}
            >
              Generate Sample Data
            </button>
          </div>
          {testResults.sampleData && (
            <div>
              <div style={{ 
                color: getStatusColor(testResults.sampleData.status),
                fontWeight: '500',
                marginBottom: '0.5rem'
              }}>
                {testResults.sampleData.message}
              </div>
              {testResults.sampleData.note && (
                <div style={{ fontSize: '0.875rem', color: '#64748b' }}>
                  {testResults.sampleData.note}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Navigation */}
        <div className="card">
          <h3 className="card-title">🧭 Navigation</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <a href="/test-phase1" className="btn btn-secondary" style={{ textDecoration: 'none' }}>
              🧪 Phase 1 Tests
            </a>
            <a href="/history" className="btn btn-secondary" style={{ textDecoration: 'none' }}>
              📋 Properties List
            </a>
            <a href="/advertisers" className="btn btn-secondary" style={{ textDecoration: 'none' }}>
              🏢 Advertisers
            </a>
            {selectedProperty && (
              <a href={`/property/${selectedProperty}`} className="btn btn-primary" style={{ textDecoration: 'none' }}>
                📊 View Selected Property
              </a>
            )}
          </div>
        </div>
      </div>

      {/* Instructions */}
      <div style={{ 
        marginTop: '2rem', 
        padding: '1rem', 
        backgroundColor: '#fef3c7', 
        borderRadius: '8px',
        fontSize: '0.875rem'
      }}>
        <div style={{ fontWeight: '600', marginBottom: '0.5rem' }}>
          📖 How to Test Phase 2:
        </div>
        <ol style={{ marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
          <li>Select a property from the dropdown</li>
          <li>Click "Run All Tests" to check all Phase 2 functionality</li>
          <li>Check individual test results for any issues</li>
          <li>Click "View Analytics" to see the Phase 2 dashboard in action</li>
          <li>Re-analyze some properties to generate price changes over time</li>
        </ol>
      </div>
    </div>
  );
};

export default TestPhase2;