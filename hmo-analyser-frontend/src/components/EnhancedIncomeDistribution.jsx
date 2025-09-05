import React, { useState } from 'react';
import { TrendingUp, BarChart3, Calendar, DollarSign, Target } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';

const EnhancedIncomeDistribution = ({ cityData }) => {
  const [showDistribution, setShowDistribution] = useState(false);
  const [activeTab, setActiveTab] = useState('monthly');
  const [chartType, setChartType] = useState('bar'); // bar, pie, line
  const [selectedRange, setSelectedRange] = useState(null);
  
  const handleRangeClick = (data) => {
  setSelectedRange(selectedRange?.id === data.id ? null : data);
};

  // Process property data for distributions
  const processPropertyData = () => {
    const propertiesWithIncome = cityData.properties.filter(p => p.monthly_income && p.monthly_income > 0);
    
    return propertiesWithIncome.map(p => ({
      address: p.address,
      monthlyIncome: p.monthly_income,
      yearlyIncome: p.monthly_income * 12,
      totalRooms: p.total_rooms || 1,
      avgRentPerRoom: p.monthly_income / (p.total_rooms || 1)
    }));
  };

  const propertyData = processPropertyData();

  // Replace the existing createDistribution function with this:
  const createFixedRanges = (data, type) => {
    if (!data.length) return [];
    
    let values, step, prefix = '£', suffix = '';
    
    switch (type) {
      case 'monthly':
        values = data.map(p => p.monthlyIncome);
        step = 1000;
        suffix = '/month';
        break;
      case 'yearly':
        values = data.map(p => p.yearlyIncome);
        step = 5000;
        suffix = '/year';
        break;
      case 'perroom':
        values = data.map(p => p.avgRentPerRoom);
        step = 100;
        suffix = '/room';
        break;
      default:
        return [];
    }
    
    const minValue = Math.min(...values);
    const maxValue = Math.max(...values);
    
    const startRange = Math.floor(minValue / step) * step;
    const endRange = Math.ceil(maxValue / step) * step;
    
    const ranges = [];
    for (let i = startRange; i < endRange; i += step) {
      const min = i;
      const max = i + step - 1;
      
      let label;
      if (step >= 1000) {
        const minK = min / 1000;
        const maxK = max / 1000;
        // Use integers only for thousands
        label = `£${Math.floor(minK)}k-${Math.floor(maxK)}k`;
      } else {
        label = `£${min}-${max}`;
      }
      
      ranges.push({
        id: i,
        label,
        min,
        max: i + step,
        suffix,
        step
      });
    }
    
    return ranges;
  };
    
  // Get distributions for each metric
  const tabs = [
    { key: 'monthly', label: 'Monthly Income', icon: DollarSign },
    { key: 'yearly', label: 'Yearly Income', icon: Calendar },
    { key: 'perroom', label: 'Rent Per Room', icon: BarChart3 }
  ];

  // Replace the existing colors array with earthy colors
  const earthyColors = {
    sage: '#8B9A7A',
    terracotta: '#C17B5C', 
    sand: '#D4C4A0',
    clay: '#A67C52',
    moss: '#7A8471',
    cream: '#F5F1E8',
    stone: '#8D7B68',
    rust: '#B5704D'
  };

  const colors = [earthyColors.sage, earthyColors.terracotta, earthyColors.sand, earthyColors.clay, earthyColors.moss, earthyColors.rust];

  // Add this after the colors array:
  const ranges = createFixedRanges(propertyData, activeTab);

  const currentDistribution = ranges.map((range, index) => {
    let propertiesInRange;
    
    switch (activeTab) {
      case 'monthly':
        propertiesInRange = propertyData.filter(p => 
          p.monthlyIncome >= range.min && p.monthlyIncome < range.max
        );
        break;
      case 'yearly':
        propertiesInRange = propertyData.filter(p => 
          p.yearlyIncome >= range.min && p.yearlyIncome < range.max
        );
        break;
      case 'perroom':
        propertiesInRange = propertyData.filter(p => 
          p.avgRentPerRoom >= range.min && p.avgRentPerRoom < range.max
        );
        break;
      default:
        propertiesInRange = [];
    }
    
    const count = propertiesInRange.length;
    const percentage = propertyData.length > 0 ? (count / propertyData.length) * 100 : 0;
    
    return {
      ...range,
      count,
      percentage: Math.round(percentage * 10) / 10,
      properties: propertiesInRange,
      color: colors[index % colors.length]
    };
  }).filter(range => range.count > 0);

  const getCurrentStats = () => {
    const currentData = propertyData;
    const getValue = (item) => {
      switch (activeTab) {
        case 'monthly': return item.monthlyIncome;
        case 'yearly': return item.yearlyIncome;
        case 'perroom': return item.avgRentPerRoom;
        default: return item.monthlyIncome;
      }
    };

    const values = currentData.map(getValue).sort((a, b) => a - b);
    const sum = values.reduce((acc, val) => acc + val, 0);

    return {
      total: values.length,
      average: values.length > 0 ? sum / values.length : 0,
      median: values.length > 0 ? values[Math.floor(values.length / 2)] : 0,
      min: values.length > 0 ? values[0] : 0,
      max: values.length > 0 ? values[values.length - 1] : 0
    };
  };

  const stats = getCurrentStats();

  if (!showDistribution) {
    // Show button to open distribution
    return (
      <div style={{
        backgroundColor: earthyColors.cream,
        borderRadius: '8px',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        border: '1px solid #e5e7eb',
        marginBottom: '32px'
      }}>
        <div style={{
          padding: '24px',
          borderBottom: '1px solid #e5e7eb'
        }}>
          <h2 style={{
            fontSize: '1.25rem',
            fontWeight: '600',
            color: '#111827',
            display: 'flex',
            alignItems: 'center',
            marginBottom: '16px'
          }}>
            <TrendingUp style={{ width: '20px', height: '20px', marginRight: '8px', color: '#059669' }} />
            Income Distribution Analysis
          </h2>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: '16px',
            marginBottom: '24px'
          }}>
            <div style={{
              textAlign: 'center',
              padding: '16px',
              backgroundColor: '#f0fdf4',
              borderRadius: '8px',
              border: '1px solid #059669'
            }}>
              <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#059669' }}>
                £{Math.round(propertyData.reduce((sum, p) => sum + p.monthlyIncome, 0) / propertyData.length || 0).toLocaleString()}
              </div>
              <div style={{ fontSize: '12px', color: '#059669', fontWeight: '500' }}>Avg Monthly</div>
            </div>

            <div style={{
              textAlign: 'center',
              padding: '16px',
              backgroundColor: '#f0f9ff',
              borderRadius: '8px',
              border: '1px solid #0ea5e9'
            }}>
              <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#0ea5e9' }}>
                £{Math.round(propertyData.reduce((sum, p) => sum + p.yearlyIncome, 0) / propertyData.length || 0).toLocaleString()}
              </div>
              <div style={{ fontSize: '12px', color: '#0ea5e9', fontWeight: '500' }}>Avg Yearly</div>
            </div>

            <div style={{
              textAlign: 'center',
              padding: '16px',
              backgroundColor: '#faf5ff',
              borderRadius: '8px',
              border: '1px solid #7c3aed'
            }}>
              <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#7c3aed' }}>
                £{Math.round(propertyData.reduce((sum, p) => sum + p.avgRentPerRoom, 0) / propertyData.length || 0)}
              </div>
              <div style={{ fontSize: '12px', color: '#7c3aed', fontWeight: '500' }}>Avg Per Room</div>
            </div>

            <div style={{
              textAlign: 'center',
              padding: '16px',
              backgroundColor: '#fef3c7',
              borderRadius: '8px',
              border: '1px solid #f59e0b'
            }}>
              <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#f59e0b' }}>
                {propertyData.length}
              </div>
              <div style={{ fontSize: '12px', color: '#f59e0b', fontWeight: '500' }}>Properties</div>
            </div>
          </div>

          <button
            onClick={() => setShowDistribution(true)}
            style={{
              width: '100%',
              padding: '12px',
              backgroundColor: '#059669',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '16px',
              fontWeight: '600',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              transition: 'background-color 0.2s'
            }}
            onMouseEnter={(e) => e.target.style.backgroundColor = '#047857'}
            onMouseLeave={(e) => e.target.style.backgroundColor = '#059669'}
          >
            <BarChart3 style={{ width: '20px', height: '20px' }} />
            View Distribution Analysis
          </button>
        </div>
      </div>
    );
  }

  // Show full distribution interface
  return (
    <div style={{
      backgroundColor: 'white',
      borderRadius: '8px',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
      border: '1px solid #e5e7eb',
      marginBottom: '32px'
    }}>
      <div style={{
        padding: '24px',
        borderBottom: '1px solid #e5e7eb'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '20px'
        }}>
          <h2 style={{
            fontSize: '1.25rem',
            fontWeight: '600',
            color: '#111827',
            display: 'flex',
            alignItems: 'center'
          }}>
            <TrendingUp style={{ width: '20px', height: '20px', marginRight: '8px', color: '#059669' }} />
            Income Distribution Analysis
          </h2>

          <button
            onClick={() => setShowDistribution(false)}
            style={{
              padding: '6px 12px',
              backgroundColor: '#f3f4f6',
              color: '#6b7280',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              fontSize: '14px',
              cursor: 'pointer'
            }}
          >
            Hide Distribution
          </button>
        </div>

        {/* Tab Navigation */}
        <div style={{
          display: 'flex',
          backgroundColor: '#f3f4f6',
          borderRadius: '8px',
          padding: '4px',
          marginBottom: '20px'
        }}>
          {tabs.map(tab => {
            const IconComponent = tab.icon;
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                style={{
                  flex: 1,
                  padding: '8px 16px',
                  border: 'none',
                  borderRadius: '6px',
                  fontSize: '14px',
                  fontWeight: '500',
                  cursor: 'pointer',
                  backgroundColor: activeTab === tab.key ? 'white' : 'transparent',
                  color: activeTab === tab.key ? '#059669' : '#6b7280',
                  boxShadow: activeTab === tab.key ? '0 1px 2px rgba(0, 0, 0, 0.05)' : 'none',
                  transition: 'all 0.2s',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px'
                }}
              >
                <IconComponent style={{ width: '16px', height: '16px' }} />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Chart Type Selector */}
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          marginBottom: '20px'
        }}>
          <div style={{
            display: 'flex',
            background: '#f3f4f6',
            borderRadius: '8px',
            padding: '4px'
          }}>
            {[
              { key: 'bar', label: 'Bar Chart', icon: <BarChart3 size={16} /> },
              { key: 'pie', label: 'Pie Chart', icon: <TrendingUp size={16} /> }
            ].map(type => (
              <button
                key={type.key}
                onClick={() => setChartType(type.key)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '8px 16px',
                  border: 'none',
                  borderRadius: '6px',
                  background: chartType === type.key ? 'white' : 'transparent',
                  color: chartType === type.key ? earthyColors.stone : '#6b7280',
                  fontSize: '14px',
                  fontWeight: '500',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
              >
                {type.icon}
                {type.label}
              </button>
            ))}
          </div>
        </div>

        {/* Stats Summary */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))',
          gap: '12px',
          marginBottom: '24px'
        }}>
          <div style={{ textAlign: 'center', padding: '8px', backgroundColor: '#f8fafc', borderRadius: '6px' }}>
            <div style={{ fontSize: '1.1rem', fontWeight: '600', color: '#111827' }}>
              £{Math.round(stats.average).toLocaleString()}
            </div>
            <div style={{ fontSize: '11px', color: '#6b7280' }}>Average</div>
          </div>
          <div style={{ textAlign: 'center', padding: '8px', backgroundColor: '#f8fafc', borderRadius: '6px' }}>
            <div style={{ fontSize: '1.1rem', fontWeight: '600', color: '#111827' }}>
              £{Math.round(stats.median).toLocaleString()}
            </div>
            <div style={{ fontSize: '11px', color: '#6b7280' }}>Median</div>
          </div>
          <div style={{ textAlign: 'center', padding: '8px', backgroundColor: '#f8fafc', borderRadius: '6px' }}>
            <div style={{ fontSize: '1.1rem', fontWeight: '600', color: '#111827' }}>
              £{Math.round(stats.min).toLocaleString()}
            </div>
            <div style={{ fontSize: '11px', color: '#6b7280' }}>Minimum</div>
          </div>
          <div style={{ textAlign: 'center', padding: '8px', backgroundColor: '#f8fafc', borderRadius: '6px' }}>
            <div style={{ fontSize: '1.1rem', fontWeight: '600', color: '#111827' }}>
              £{Math.round(stats.max).toLocaleString()}
            </div>
            <div style={{ fontSize: '11px', color: '#6b7280' }}>Maximum</div>
          </div>
          <div style={{ textAlign: 'center', padding: '8px', backgroundColor: '#f8fafc', borderRadius: '6px' }}>
            <div style={{ fontSize: '1.1rem', fontWeight: '600', color: '#111827' }}>
              {stats.total}
            </div>
            <div style={{ fontSize: '11px', color: '#6b7280' }}>Properties</div>
          </div>
        </div>
      </div>

      <div style={{ padding: '24px' }}>
        {/* Distribution Chart */}
        <div style={{ marginBottom: '24px' }}>
          <h3 style={{
            fontSize: '1rem',
            fontWeight: '600',
            color: earthyColors.stone,
            marginBottom: '16px',
            textAlign: 'center'
          }}>
            {tabs.find(t => t.key === activeTab)?.label} Distribution
          </h3>
          
          <ResponsiveContainer width="100%" height={400}>
            {chartType === 'bar' ? (
              <BarChart data={currentDistribution}>
                <CartesianGrid strokeDasharray="3 3" stroke={earthyColors.stone + '30'} />
                <XAxis dataKey="label" angle={-45} textAnchor="end" height={80} stroke={earthyColors.stone} />
                <YAxis stroke={earthyColors.stone} />
                <Tooltip 
                  contentStyle={{
                    background: 'rgba(255, 255, 255, 0.95)',
                    backdropFilter: 'blur(10px)',
                    border: `2px solid ${earthyColors.sage}`,
                    borderRadius: '8px'
                  }}
                  formatter={(value, name) => [
                    name === 'count' ? `${value} properties` : `${value}%`,
                    name === 'count' ? 'Properties' : 'Percentage'
                  ]}
                />
                <Bar 
                  dataKey="count" 
                  radius={[4, 4, 0, 0]}
                  onClick={handleRangeClick}
                  style={{ cursor: 'pointer' }}
                >
                  {currentDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                  ))}
                </Bar>
              </BarChart>
            ) : (
              <PieChart>
                <Pie
                  data={currentDistribution}
                  cx="50%"
                  cy="50%"
                  outerRadius={120}
                  innerRadius={40}
                  paddingAngle={2}
                  dataKey="count"
                >
                  {currentDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{
                    background: 'rgba(255, 255, 255, 0.95)',
                    backdropFilter: 'blur(10px)',
                    border: `2px solid ${earthyColors.sage}`,
                    borderRadius: '8px'
                  }}
                />
              </PieChart>
            )}
          </ResponsiveContainer>
        </div>

        {/* Distribution Table */}
        <div>
          <h3 style={{
            fontSize: '1rem',
            fontWeight: '600',
            color: '#374151',
            marginBottom: '16px'
          }}>
            Distribution Breakdown
          </h3>
          
          <div style={{
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            overflow: 'hidden'
          }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#f9fafb' }}>
                  <th style={{ padding: '12px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#374151' }}>
                    Range
                  </th>
                  <th style={{ padding: '12px', textAlign: 'right', fontSize: '12px', fontWeight: '600', color: '#374151' }}>
                    Properties
                  </th>
                  <th style={{ padding: '12px', textAlign: 'right', fontSize: '12px', fontWeight: '600', color: '#374151' }}>
                    Percentage
                  </th>
                  <th style={{ padding: '12px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#374151' }}>
                    Visual
                  </th>
                </tr>
              </thead>
              <tbody>
                {currentDistribution.map((range, index) => (
                  <tr key={range.label} style={{ borderBottom: index < currentDistribution.length - 1 ? '1px solid #f3f4f6' : 'none' }}>
                    <td style={{ padding: '12px', fontSize: '14px', color: '#111827', fontWeight: '500' }}>
                      {range.label}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'right', fontSize: '14px', color: '#111827' }}>
                      {range.count}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'right', fontSize: '14px', color: '#111827' }}>
                      {range.percentage.toFixed(1)}%
                    </td>
                    <td style={{ padding: '12px' }}>
                      <div style={{
                        width: '100%',
                        height: '8px',
                        backgroundColor: '#f3f4f6',
                        borderRadius: '4px',
                        overflow: 'hidden'
                      }}>
                        <div style={{
                          width: `${range.percentage}%`,
                          height: '100%',
                          backgroundColor: colors[index % colors.length],
                          borderRadius: '4px'
                        }} />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>


        {/* Selected Range Details */}
        {selectedRange && (
          <div style={{
            marginTop: '24px',
            padding: '20px',
            background: `${selectedRange.color}08`,
            borderRadius: '12px',
            border: `2px solid ${selectedRange.color}`
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              marginBottom: '16px'
            }}>
              <div style={{
                width: '16px',
                height: '16px',
                borderRadius: '4px',
                background: selectedRange.color
              }} />
              <h4 style={{
                fontSize: '1.1rem',
                fontWeight: '600',
                color: earthyColors.stone,
                margin: 0
              }}>
                Properties in {selectedRange.label} range
              </h4>
              <span style={{
                background: `${selectedRange.color}20`,
                color: selectedRange.color,
                padding: '4px 8px',
                borderRadius: '8px',
                fontSize: '12px',
                fontWeight: '600'
              }}>
                {selectedRange.count} properties
              </span>
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
              gap: '12px'
            }}>
              {selectedRange.properties.map((property, index) => (
                <div
                  key={property.address}
                  style={{
                    padding: '16px',
                    background: 'white',
                    borderRadius: '8px',
                    border: `1px solid ${selectedRange.color}30`,
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <div>
                    <div style={{
                      fontSize: '14px',
                      fontWeight: '600',
                      color: earthyColors.stone,
                      marginBottom: '4px'
                    }}>
                      {property.address.split(',')[0]}
                    </div>
                    <div style={{
                      fontSize: '12px',
                      color: earthyColors.stone + '70'
                    }}>
                      {property.totalRooms} rooms
                    </div>
                  </div>
                  <div style={{
                    textAlign: 'right'
                  }}>
                    <div style={{
                      fontSize: '14px',
                      fontWeight: '700',
                      color: selectedRange.color
                    }}>
                      £{activeTab === 'monthly' 
                        ? property.monthlyIncome.toLocaleString()
                        : activeTab === 'yearly'
                        ? property.yearlyIncome.toLocaleString()
                        : Math.round(property.avgRentPerRoom).toLocaleString()
                      }
                    </div>
                    <div style={{
                      fontSize: '10px',
                      color: earthyColors.stone + '60'
                    }}>
                      {selectedRange.suffix}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Summary Insights */}
        <div style={{
          marginTop: '24px',
          padding: '16px',
          backgroundColor: '#f0f9ff',
          borderRadius: '8px',
          border: '1px solid #0ea5e9'
        }}>
          <h4 style={{
            fontSize: '14px',
            fontWeight: '600',
            color: '#0369a1',
            marginBottom: '8px'
          }}>
            Key Insights
          </h4>
          <div style={{ fontSize: '12px', color: '#0369a1' }}>
            <div style={{ marginBottom: '4px' }}>
              <strong>Range Spread:</strong> £{(stats.max - stats.min).toLocaleString()} difference between highest and lowest
            </div>
            <div style={{ marginBottom: '4px' }}>
              <strong>Most Common Range:</strong> {currentDistribution.reduce((max, range) => range.count > max.count ? range : max, { count: 0, label: 'N/A' }).label}
            </div>
            <div>
              <strong>Distribution:</strong> {currentDistribution.length} ranges across {stats.total} properties
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedIncomeDistribution;