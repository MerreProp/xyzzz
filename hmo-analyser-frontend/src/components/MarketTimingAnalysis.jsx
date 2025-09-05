// File: src/components/MarketTimingAnalysis.jsx
// Market Timing Analysis Component for Individual City Analysis

import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Clock, TrendingUp, TrendingDown, Activity, Calendar } from 'lucide-react';

const MarketTimingAnalysis = ({ cityData }) => {
  const [timingData, setTimingData] = useState(null);
  const [velocityMetrics, setVelocityMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedPeriod, setSelectedPeriod] = useState('weekly');
  const [selectedDays, setSelectedDays] = useState(90);

  const cityName = cityData?.name?.toLowerCase().replace(/\s+/g, '-');

  useEffect(() => {
    if (!cityName) return;

    const fetchTimingData = async () => {
      setLoading(true);
      try {
        // Fetch market timing data
        const timingResponse = await fetch(
          `/api/cities/${cityName}/market-timing?period=${selectedPeriod}&days=${selectedDays}`
        );
        const timingResult = await timingResponse.json();

        // Fetch velocity metrics
        const velocityResponse = await fetch(
          `/api/cities/${cityName}/velocity-metrics?days=30`
        );
        const velocityResult = await velocityResponse.json();

        setTimingData(timingResult);
        setVelocityMetrics(velocityResult);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch market timing data:', err);
        setError('Failed to load market timing data');
      } finally {
        setLoading(false);
      }
    };

    fetchTimingData();
  }, [cityName, selectedPeriod, selectedDays]);

  if (loading) {
    return (
      <div style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        padding: '24px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
        marginBottom: '24px'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          marginBottom: '20px'
        }}>
          <Clock style={{ width: '20px', height: '20px', marginRight: '8px', color: '#ea580c' }} />
          <h3 style={{
            fontSize: '1.125rem',
            fontWeight: '600',
            color: '#111827',
            margin: 0
          }}>
            Market Timing Analysis
          </h3>
        </div>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '200px'
        }}>
          <div style={{
            width: '32px',
            height: '32px',
            border: '2px solid #e5e7eb',
            borderTop: '2px solid #ea580c',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }}></div>
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

  if (error) {
    return (
      <div style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        padding: '24px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
        marginBottom: '24px'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          marginBottom: '20px'
        }}>
          <Clock style={{ width: '20px', height: '20px', marginRight: '8px', color: '#ea580c' }} />
          <h3 style={{
            fontSize: '1.125rem',
            fontWeight: '600',
            color: '#111827',
            margin: 0
          }}>
            Market Timing Analysis
          </h3>
        </div>
        <div style={{
          textAlign: 'center',
          color: '#ef4444',
          padding: '40px'
        }}>
          {error}
        </div>
      </div>
    );
  }

  const velocityTrend = velocityMetrics?.velocity_trend;
  const velocityColor = velocityTrend === 'increasing' ? '#059669' : 
                       velocityTrend === 'decreasing' ? '#dc2626' : '#6b7280';

  const TrendIcon = velocityTrend === 'increasing' ? TrendingUp :
                   velocityTrend === 'decreasing' ? TrendingDown : Activity;

  return (
    <div style={{
      backgroundColor: 'white',
      borderRadius: '8px',
      padding: '24px',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
      marginBottom: '24px'
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '24px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <Clock style={{ width: '20px', height: '20px', marginRight: '8px', color: '#ea580c' }} />
          <h3 style={{
            fontSize: '1.125rem',
            fontWeight: '600',
            color: '#111827',
            margin: 0
          }}>
            Market Timing Analysis
          </h3>
        </div>

        {/* Controls */}
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(e.target.value)}
            style={{
              padding: '4px 8px',
              border: '1px solid #d1d5db',
              borderRadius: '4px',
              fontSize: '14px'
            }}
          >
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
          </select>
          
          <select
            value={selectedDays}
            onChange={(e) => setSelectedDays(Number(e.target.value))}
            style={{
              padding: '4px 8px',
              border: '1px solid #d1d5db',
              borderRadius: '4px',
              fontSize: '14px'
            }}
          >
            <option value={30}>30 days</option>
            <option value={60}>60 days</option>
            <option value={90}>90 days</option>
            <option value={180}>180 days</option>
          </select>
        </div>
      </div>

      {/* Key Metrics Row */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px',
        marginBottom: '24px'
      }}>
        {/* Average Time on Market */}
        <div style={{
          padding: '16px',
          backgroundColor: '#f8fafc',
          borderRadius: '6px',
          border: '1px solid #e2e8f0'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            marginBottom: '8px'
          }}>
            <Clock style={{ width: '16px', height: '16px', marginRight: '6px', color: '#ea580c' }} />
            <span style={{ fontSize: '14px', fontWeight: '500', color: '#374151' }}>
              Avg Time on Market
            </span>
          </div>
          <div style={{ fontSize: '24px', fontWeight: '700', color: '#111827' }}>
            {timingData?.avg_time_on_market_days ? 
              `${timingData.avg_time_on_market_days} days` : 'N/A'}
          </div>
        </div>

        {/* Market Velocity */}
        <div style={{
          padding: '16px',
          backgroundColor: '#f8fafc',
          borderRadius: '6px',
          border: '1px solid #e2e8f0'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            marginBottom: '8px'
          }}>
            <TrendIcon style={{ width: '16px', height: '16px', marginRight: '6px', color: velocityColor }} />
            <span style={{ fontSize: '14px', fontWeight: '500', color: '#374151' }}>
              Market Velocity
            </span>
          </div>
          <div style={{ fontSize: '24px', fontWeight: '700', color: velocityColor }}>
            {velocityMetrics?.daily_velocity?.net_velocity_per_day ?
              `${velocityMetrics.daily_velocity.net_velocity_per_day > 0 ? '+' : ''}${velocityMetrics.daily_velocity.net_velocity_per_day}/day` :
              'N/A'}
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
            {velocityTrend === 'increasing' ? 'More rooms coming available' :
             velocityTrend === 'decreasing' ? 'Fewer rooms available' : 'Stable market'}
          </div>
        </div>

        {/* Current Availability */}
        <div style={{
          padding: '16px',
          backgroundColor: '#f8fafc',
          borderRadius: '6px',
          border: '1px solid #e2e8f0'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            marginBottom: '8px'
          }}>
            <Activity style={{ width: '16px', height: '16px', marginRight: '6px', color: '#2563eb' }} />
            <span style={{ fontSize: '14px', fontWeight: '500', color: '#374151' }}>
              Currently Available
            </span>
          </div>
          <div style={{ fontSize: '24px', fontWeight: '700', color: '#111827' }}>
            {velocityMetrics?.currently_available || 0} rooms
          </div>
        </div>

        {/* Data Points */}
        <div style={{
          padding: '16px',
          backgroundColor: '#f8fafc',
          borderRadius: '6px',
          border: '1px solid #e2e8f0'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            marginBottom: '8px'
          }}>
            <Calendar style={{ width: '16px', height: '16px', marginRight: '6px', color: '#059669' }} />
            <span style={{ fontSize: '14px', fontWeight: '500', color: '#374151' }}>
              Periods Analyzed
            </span>
          </div>
          <div style={{ fontSize: '24px', fontWeight: '700', color: '#111827' }}>
            {timingData?.total_periods_analyzed || 0}
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
            from {timingData?.total_properties || 0} properties
          </div>
        </div>
      </div>

      {/* Velocity Chart */}
      {timingData?.velocity_data && timingData.velocity_data.length > 0 && (
        <div style={{ marginBottom: '24px' }}>
          <h4 style={{
            fontSize: '1rem',
            fontWeight: '600',
            color: '#111827',
            marginBottom: '16px'
          }}>
            Market Velocity Over Time
          </h4>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={timingData.velocity_data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period" />
              <YAxis />
              <Tooltip 
                formatter={(value, name) => [
                  value,
                  name === 'rooms_coming_on_market' ? 'Coming On Market' :
                  name === 'rooms_going_off_market' ? 'Going Off Market' : 'Net Change'
                ]}
              />
              <Legend />
              <Bar dataKey="rooms_coming_on_market" fill="#059669" name="Coming On Market" />
              <Bar dataKey="rooms_going_off_market" fill="#dc2626" name="Going Off Market" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Timing Trends */}
      {timingData?.timing_trends && timingData.timing_trends.length > 0 && (
        <div style={{ marginBottom: '24px' }}>
          <h4 style={{
            fontSize: '1rem',
            fontWeight: '600',
            color: '#111827',
            marginBottom: '16px'
          }}>
            Average Days on Market Trend
          </h4>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={timingData.timing_trends.filter(d => d.avg_days_on_market !== null)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period" />
              <YAxis />
              <Tooltip 
                formatter={(value) => [`${value} days`, 'Avg Days on Market']}
              />
              <Line 
                type="monotone" 
                dataKey="avg_days_on_market" 
                stroke="#ea580c" 
                strokeWidth={3}
                dot={{ fill: '#ea580c', strokeWidth: 2, r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Seasonal Patterns */}
      {timingData?.seasonal_patterns && timingData.seasonal_patterns.length > 0 && (
        <div>
          <h4 style={{
            fontSize: '1rem',
            fontWeight: '600',
            color: '#111827',
            marginBottom: '16px'
          }}>
            Seasonal Patterns
          </h4>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={timingData.seasonal_patterns}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip 
                formatter={(value, name) => [
                  name === 'avg_days_on_market' ? `${value} days` : value,
                  name === 'avg_days_on_market' ? 'Avg Days on Market' : 'Total Periods'
                ]}
              />
              <Bar dataKey="avg_days_on_market" fill="#ea580c" name="Avg Days on Market" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Summary */}
      <div style={{
        marginTop: '20px',
        padding: '16px',
        backgroundColor: '#fef3c7',
        borderRadius: '6px',
        border: '1px solid #f59e0b'
      }}>
        <div style={{ fontSize: '14px', color: '#92400e' }}>
          <strong>Market Summary:</strong> {timingData?.city} has an average time on market of{' '}
          <strong>{timingData?.avg_time_on_market_days || 'N/A'} days</strong>. 
          The market velocity is currently{' '}
          <strong style={{ color: velocityColor }}>{velocityTrend}</strong>
          {velocityMetrics?.daily_velocity?.net_velocity_per_day && 
            ` with ${Math.abs(velocityMetrics.daily_velocity.net_velocity_per_day)} rooms per day net change`}.
        </div>
      </div>
    </div>
  );
};

export default MarketTimingAnalysis;