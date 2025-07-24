
import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

// Phase 2: Price History Chart Component
const PriceHistoryChart = ({ propertyId }) => {
  const [priceData, setPriceData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPriceData = async () => {
      try {
        setIsLoading(true);
        const response = await fetch(`/api/properties/${propertyId}/price-trends`);
        if (!response.ok) {
          throw new Error('Failed to fetch price data');
        }
        const data = await response.json();
        setPriceData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    if (propertyId) {
      fetchPriceData();
    }
  }, [propertyId]);

  if (error) {
    return (
      <div style={{ 
        padding: '2rem', 
        textAlign: 'center', 
        backgroundColor: '#fee2e2', 
        borderRadius: '8px',
        border: '1px solid #fecaca'
      }}>
        <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>❌</div>
        <h4 style={{ color: '#dc2626', marginBottom: '0.5rem' }}>Error Loading Price Data</h4>
        <p style={{ color: '#991b1b', fontSize: '0.875rem' }}>{error}</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <div className="spinner" style={{ width: '30px', height: '30px', margin: '0 auto' }}></div>
        <p>Loading price history...</p>
      </div>
    );
  }

  if (!priceData || priceData.total_changes === 0) {
    return (
      <div style={{ 
        padding: '2rem', 
        textAlign: 'center', 
        backgroundColor: '#f8fafc', 
        borderRadius: '8px',
        border: '1px dashed #cbd5e1'
      }}>
        <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>📈</div>
        <h4 style={{ color: '#64748b', marginBottom: '0.5rem' }}>No Price Changes Yet</h4>
        <p style={{ color: '#64748b', fontSize: '0.875rem' }}>
          Price history will appear here as rooms are re-analyzed with different prices.
        </p>
      </div>
    );
  }

  // Transform data for chart
  const chartData = [];
  Object.entries(priceData.changes_by_room).forEach(([roomId, changes]) => {
    changes.forEach(change => {
      chartData.push({
        date: new Date(change.date).toLocaleDateString('en-GB'),
        room: `Room ${roomId.slice(-4)}`,
        price: change.new_price,
        previousPrice: change.previous_price,
        changeAmount: change.change_amount
      });
    });
  });

  // Sort by date
  chartData.sort((a, b) => new Date(a.date) - new Date(b.date));

  return (
    <div className="card">
      <h3 className="card-title">💰 Price History Analysis</h3>
      
      {/* Summary Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        <div style={{ padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '8px', textAlign: 'center' }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#059669' }}>
            {priceData.total_changes}
          </div>
          <div style={{ fontSize: '0.875rem', color: '#64748b' }}>Total Changes</div>
        </div>
        
        <div style={{ padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '8px', textAlign: 'center' }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: priceData.average_change_amount > 0 ? '#059669' : '#dc2626' }}>
            £{Math.abs(priceData.average_change_amount)}
          </div>
          <div style={{ fontSize: '0.875rem', color: '#64748b' }}>Avg Change</div>
        </div>
        
        <div style={{ padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '8px', textAlign: 'center' }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#667eea' }}>
            {priceData.trend_direction === 'increasing' ? '📈' : 
             priceData.trend_direction === 'decreasing' ? '📉' : '➡️'}
          </div>
          <div style={{ fontSize: '0.875rem', color: '#64748b' }}>
            {priceData.trend_direction.charAt(0).toUpperCase() + priceData.trend_direction.slice(1)}
          </div>
        </div>
        
        <div style={{ padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '8px', textAlign: 'center' }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#f59e0b' }}>
            £{priceData.price_volatility}
          </div>
          <div style={{ fontSize: '0.875rem', color: '#64748b' }}>Volatility</div>
        </div>
      </div>

      {/* Price Chart */}
      <div style={{ height: '300px', marginBottom: '1rem' }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis 
              domain={['dataMin - 50', 'dataMax + 50']}
              tickFormatter={(value) => `£${value}`}
            />
            <Tooltip 
              formatter={(value, name) => [`£${value}`, name]}
              labelFormatter={(label) => `Date: ${label}`}
            />
            <Line 
              type="monotone" 
              dataKey="price" 
              stroke="#667eea" 
              strokeWidth={2}
              dot={{ fill: '#667eea', strokeWidth: 2, r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div style={{ fontSize: '0.875rem', color: '#64748b', textAlign: 'center' }}>
        Showing price changes over the last {priceData.period_days} days
      </div>
    </div>
  );
};

// Phase 2: Timeline Visualization Component
const AvailabilityTimeline = ({ propertyId }) => {
  const [timelineData, setTimelineData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedTimeframe, setSelectedTimeframe] = useState('3months');

  useEffect(() => {
    const fetchTimelineData = async () => {
      try {
        setIsLoading(true);
        const timeframes = {
          '1month': 30,
          '3months': 90,
          '6months': 180,
          '1year': 365
        };
        const days = timeframes[selectedTimeframe] || 90;
        
        const response = await fetch(`/api/properties/${propertyId}/availability-timeline?days=${days}`);
        if (!response.ok) {
          throw new Error('Failed to fetch timeline data');
        }
        const data = await response.json();
        setTimelineData(data);
      } catch (err) {
        console.error('Error fetching timeline:', err);
        setTimelineData({ error: err.message });
      } finally {
        setIsLoading(false);
      }
    };

    if (propertyId) {
      fetchTimelineData();
    }
  }, [propertyId, selectedTimeframe]);

  if (isLoading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <div className="spinner" style={{ width: '30px', height: '30px', margin: '0 auto' }}></div>
        <p>Loading availability timeline...</p>
      </div>
    );
  }

  if (!timelineData || timelineData.error) {
    return (
      <div className="card">
        <h3 className="card-title">📅 Availability Timeline</h3>
        <div style={{ 
          padding: '2rem', 
          textAlign: 'center', 
          backgroundColor: '#f8fafc', 
          borderRadius: '8px',
          border: '1px dashed #cbd5e1'
        }}>
          <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>📊</div>
          <h4 style={{ color: '#64748b', marginBottom: '0.5rem' }}>Timeline Data Coming Soon</h4>
          <p style={{ color: '#64748b', fontSize: '0.875rem' }}>
            {timelineData?.error || "Timeline visualization will show room availability patterns over time."}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h3 className="card-title">📅 Availability Timeline</h3>
        <select 
          value={selectedTimeframe} 
          onChange={(e) => setSelectedTimeframe(e.target.value)}
          style={{ 
            padding: '0.5rem', 
            border: '1px solid #e5e7eb', 
            borderRadius: '6px',
            fontSize: '0.875rem'
          }}
        >
          <option value="1month">Last Month</option>
          <option value="3months">Last 3 Months</option>
          <option value="6months">Last 6 Months</option>
          <option value="1year">Last Year</option>
        </select>
      </div>
      
      {/* Timeline visualization would go here */}
      <div style={{ 
        height: '200px', 
        backgroundColor: '#f8fafc', 
        borderRadius: '8px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        border: '1px dashed #cbd5e1'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>🚧</div>
          <p style={{ color: '#64748b' }}>Timeline visualization in development</p>
        </div>
      </div>
    </div>
  );
};

// Phase 2: Advanced Statistics Component
const AdvancedStatistics = ({ propertyId }) => {
  const [stats, setStats] = useState(null);
  const [trends, setTrends] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setIsLoading(true);
        
        // Fetch both statistics and trends
        const [statsResponse, trendsResponse] = await Promise.all([
          fetch(`/api/properties/${propertyId}/analytics`),
          fetch(`/api/properties/${propertyId}/trends`)
        ]);
        
        if (statsResponse.ok) {
          const statsData = await statsResponse.json();
          setStats(statsData);
        }
        
        if (trendsResponse.ok) {
          const trendsData = await trendsResponse.json();
          setTrends(trendsData);
        }
        
      } catch (err) {
        console.error('Error fetching analytics:', err);
      } finally {
        setIsLoading(false);
      }
    };

    if (propertyId) {
      fetchAnalytics();
    }
  }, [propertyId]);

  if (isLoading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <div className="spinner" style={{ width: '30px', height: '30px', margin: '0 auto' }}></div>
        <p>Loading advanced analytics...</p>
      </div>
    );
  }

  return (
    <div className="card">
      <h3 className="card-title">📊 Advanced Statistics & Trends</h3>
      
      {/* Key Metrics Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        
        {/* Availability Metrics */}
        <div style={{ padding: '1.5rem', backgroundColor: '#f0f9ff', borderRadius: '8px', border: '1px solid #bae6fd' }}>
          <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🏠</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#0369a1', marginBottom: '0.25rem' }}>
            {stats?.avg_availability_duration || 'N/A'}
          </div>
          <div style={{ fontSize: '0.875rem', color: '#64748b' }}>
            Avg Availability Days
          </div>
        </div>

        {/* Turnover Rate */}
        <div style={{ padding: '1.5rem', backgroundColor: '#fef3c7', borderRadius: '8px', border: '1px solid #fed7aa' }}>
          <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🔄</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#d97706', marginBottom: '0.25rem' }}>
            {trends?.turnover_rate || 'N/A'}
          </div>
          <div style={{ fontSize: '0.875rem', color: '#64748b' }}>
            Monthly Turnover Rate
          </div>
        </div>

        {/* Income Stability */}
        <div style={{ padding: '1.5rem', backgroundColor: '#dcfce7', borderRadius: '8px', border: '1px solid #bbf7d0' }}>
          <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>💰</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#059669', marginBottom: '0.25rem' }}>
            {trends?.income_stability ? `${Math.round(trends.income_stability * 100)}%` : 'N/A'}
          </div>
          <div style={{ fontSize: '0.875rem', color: '#64748b' }}>
            Income Stability Score
          </div>
        </div>

        {/* Market Position */}
        <div style={{ padding: '1.5rem', backgroundColor: '#f3e8ff', borderRadius: '8px', border: '1px solid #d8b4fe' }}>
          <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📈</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#7c3aed', marginBottom: '0.25rem' }}>
            {trends?.market_position || 'Average'}
          </div>
          <div style={{ fontSize: '0.875rem', color: '#64748b' }}>
            Market Position
          </div>
        </div>
      </div>

      {/* Trend Charts */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem' }}>
        
        {/* Availability Trend Chart */}
        <div>
          <h4 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '1rem', color: '#1e293b' }}>
            📊 Availability Trends
          </h4>
          <div style={{ height: '200px', backgroundColor: '#f8fafc', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px dashed #cbd5e1' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>📈</div>
              <p style={{ color: '#64748b', fontSize: '0.875rem' }}>Trend chart coming soon</p>
            </div>
          </div>
        </div>

        {/* Performance Indicators */}
        <div>
          <h4 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '1rem', color: '#1e293b' }}>
            🎯 Performance Indicators
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem', backgroundColor: '#f8fafc', borderRadius: '6px' }}>
              <span style={{ fontSize: '0.875rem', color: '#64748b' }}>Demand Level</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <div style={{ 
                  width: '60px', 
                  height: '6px', 
                  backgroundColor: '#e5e7eb', 
                  borderRadius: '3px',
                  overflow: 'hidden'
                }}>
                  <div style={{ 
                    width: '75%', 
                    height: '100%', 
                    backgroundColor: '#059669',
                    borderRadius: '3px'
                  }}></div>
                </div>
                <span style={{ fontSize: '0.875rem', fontWeight: '500' }}>High</span>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem', backgroundColor: '#f8fafc', borderRadius: '6px' }}>
              <span style={{ fontSize: '0.875rem', color: '#64748b' }}>Price Competitiveness</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <div style={{ 
                  width: '60px', 
                  height: '6px', 
                  backgroundColor: '#e5e7eb', 
                  borderRadius: '3px',
                  overflow: 'hidden'
                }}>
                  <div style={{ 
                    width: '60%', 
                    height: '100%', 
                    backgroundColor: '#f59e0b',
                    borderRadius: '3px'
                  }}></div>
                </div>
                <span style={{ fontSize: '0.875rem', fontWeight: '500' }}>Medium</span>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem', backgroundColor: '#f8fafc', borderRadius: '6px' }}>
              <span style={{ fontSize: '0.875rem', color: '#64748b' }}>Occupancy Rate</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <div style={{ 
                  width: '60px', 
                  height: '6px', 
                  backgroundColor: '#e5e7eb', 
                  borderRadius: '3px',
                  overflow: 'hidden'
                }}>
                  <div style={{ 
                    width: '85%', 
                    height: '100%', 
                    backgroundColor: '#059669',
                    borderRadius: '3px'
                  }}></div>
                </div>
                <span style={{ fontSize: '0.875rem', fontWeight: '500' }}>85%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div style={{ 
        marginTop: '2rem', 
        padding: '1rem', 
        backgroundColor: '#f8fafc', 
        borderRadius: '8px',
        fontSize: '0.875rem',
        color: '#64748b'
      }}>
        💡 <strong>Note:</strong> Advanced analytics are calculated based on availability patterns, price changes, and market data. 
        More data points will improve accuracy over time.
      </div>
    </div>
  );
};

// Phase 2: Main Analytics Dashboard Component
const Phase2AnalyticsDashboard = ({ propertyId }) => {
  const [activeTab, setActiveTab] = useState('price-history');

  const tabs = [
    { id: 'price-history', label: '💰 Price History', component: PriceHistoryChart },
    { id: 'timeline', label: '📅 Timeline', component: AvailabilityTimeline },
    { id: 'statistics', label: '📊 Advanced Stats', component: AdvancedStatistics }
  ];

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component;

  return (
    <div>
      {/* Tab Navigation */}
      <div style={{ 
        display: 'flex', 
        gap: '0.5rem', 
        marginBottom: '2rem',
        borderBottom: '1px solid #e5e7eb',
        paddingBottom: '1rem'
      }}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '0.75rem 1.5rem',
              border: 'none',
              borderRadius: '8px 8px 0 0',
              backgroundColor: activeTab === tab.id ? '#667eea' : '#f1f5f9',
              color: activeTab === tab.id ? 'white' : '#64748b',
              fontWeight: activeTab === tab.id ? '600' : '500',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              fontSize: '0.875rem'
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Active Component */}
      {ActiveComponent && <ActiveComponent propertyId={propertyId} />}
    </div>
  );
};

export default Phase2AnalyticsDashboard;