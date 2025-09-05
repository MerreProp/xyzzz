import React, { useState, useEffect, useMemo } from 'react';
import { ArrowLeft, TrendingUp, MapPin, BarChart3, Clock } from 'lucide-react';
import LTVCalculator from '../components/LTVCalculator';
import MarketTimingAnalysis from '../components/MarketTimingAnalysis';
import EnhancedIncomeDistribution from '../components/EnhancedIncomeDistribution';
import { useTheme } from '../contexts/ThemeContext';
import { useDarkMode } from '../contexts/DarkModeContext';
import { 
  Download, 
  RefreshCw, 
  Calendar, 
  ChevronRight, 
  ArrowUpRight, 
  ArrowDownRight,
  Eye,
  MoreHorizontal,
  Filter,
  Users,
  Building
} from 'lucide-react';

const IndividualCityAnalysis = () => {
  const [cityData, setCityData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Add theme system
  const { currentPalette } = useTheme();
  const { isDarkMode } = useDarkMode();

  const baseColors = {
    darkSlate: '#2C3E4A',
    lightCream: '#F5F1E8',
    softGray: '#A8A5A0',
  };

  const theme = isDarkMode ? {
    background: '#1a202c',
    cardBackground: '#2d3748',
    text: baseColors.lightCream,
    textSecondary: '#a0aec0',
    border: 'rgba(255, 255, 255, 0.1)',
    accent: currentPalette.primary,
    success: '#48bb78',
    warning: '#ed8936',
    danger: '#f56565'
  } : {
    background: '#f7fafc',
    cardBackground: '#ffffff',
    text: baseColors.darkSlate,
    textSecondary: baseColors.softGray,
    border: '#e2e8f0',
    accent: currentPalette.primary,
    success: '#38a169',
    warning: '#d69e2e',
    danger: '#e53e3e'
  };

  // Helper function to capitalize city name
  const capitalizeCityName = (name) => {
    if (!name) return 'City';
    return name.charAt(0).toUpperCase() + name.slice(1).toLowerCase();
  };

  useEffect(() => {
    const fetchCityData = async () => {
      try {
        console.log('🏙️ Loading individual city analysis...');
        
        // Get city name from URL
        const urlPath = window.location.pathname;
        const encodedCityName = urlPath.split('/').pop();
        const decodedCityName = decodeURIComponent(encodedCityName);
        
        console.log(`🎯 Loading data for city: ${decodedCityName}`);

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

        console.log(`📊 Total properties loaded: ${allProperties.length}`);

        // Extract city from address function
        const extractCityFromAddress = (address) => {
          if (!address) return null;
          const addressParts = address.split(',').map(part => part.trim());
          
          // Check each part of the address for city name
          for (const part of addressParts) {
            if (part.toLowerCase() === decodedCityName.toLowerCase()) {
              return decodedCityName;
            }
          }
          return null;
        };

        // Filter properties for this city
        const cityProperties = allProperties.filter(property => {
          const propertyCity = extractCityFromAddress(property.address);
          return propertyCity === decodedCityName;
        });

        console.log(`🏠 Properties found for ${decodedCityName}: ${cityProperties.length}`);

        if (cityProperties.length === 0) {
          setError(`No properties found for ${decodedCityName}`);
          setLoading(false);
          return;
        }

        // Calculate city metrics
        let totalIncome = 0;
        let propertiesWithIncome = 0;
        let recentlyUpdated = 0;
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

        cityProperties.forEach(property => {
          if (property.monthly_income && property.monthly_income > 0) {
            totalIncome += property.monthly_income;
            propertiesWithIncome++;
          }
          
          if (property.updated_at && new Date(property.updated_at) > thirtyDaysAgo) {
            recentlyUpdated++;
          }
        });

        const avgIncome = propertiesWithIncome > 0 ? Math.round(totalIncome / propertiesWithIncome) : 0;

        // Get areas for this city
        const areasResponse = await fetch(`/api/filters/areas/${encodeURIComponent(decodedCityName)}`);
        const areasData = await areasResponse.json();
        const areas = areasData.areas || [];

        const finalCityData = {
          name: decodedCityName,
          propertyCount: cityProperties.length,
          avgIncome,
          totalIncome: Math.round(totalIncome),
          propertiesWithIncome,
          recentlyUpdated,
          areas,
          properties: cityProperties
        };

        console.log(`✅ City data compiled:`, finalCityData);
        setCityData(finalCityData);
        setLoading(false);

      } catch (error) {
        console.error('❌ Error loading city data:', error);
        setError(`Failed to load city data: ${error.message}`);
        setLoading(false);
      }
    };

    fetchCityData();
  }, []);

  const handleBackToSelection = () => {
    window.location.href = '/cityanalysis';
  };

  // Reusable Metric Card Component
  const MetricCard = ({ title, value, subtitle, icon, color, theme }) => {

    if (!theme) {
      console.error('MetricCard: theme prop is undefined');
      return null;
    }
  
    const colorClasses = {
      blue: currentPalette.primary,
      green: '#10b981',
      orange: '#f59e0b',
      purple: '#8b5cf6'
    };
    
    const cardColor = colorClasses[color];

    return (
      <div
        style={{
          padding: '1.25rem',
          backgroundColor: isDarkMode ? 'rgba(255, 255, 255, 0.03)' : '#f8fafc',
          borderRadius: '10px',
          border: `1px solid ${theme.border}`,
          transition: 'all 0.2s ease',
          cursor: 'default',
          position: 'relative',
          overflow: 'hidden'
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'translateY(-1px)';
          e.currentTarget.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.1)';
          e.currentTarget.style.borderColor = cardColor;
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'translateY(0px)';
          e.currentTarget.style.boxShadow = 'none';
          e.currentTarget.style.borderColor = theme.border;
        }}
      >
        {/* Background gradient accent */}
        <div style={{
          position: 'absolute',
          top: 0,
          right: 0,
          width: '50px',
          height: '50px',
          background: `linear-gradient(135deg, ${cardColor}12, ${cardColor}03)`,
          borderRadius: '0 10px 0 100%',
          pointerEvents: 'none'
        }} />
        
        <div style={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          marginBottom: '0.75rem',
          position: 'relative',
          zIndex: 1
        }}>
          <div style={{ flex: 1 }}>
            <h3 style={{
              fontSize: '0.75rem',
              fontWeight: '500',
              color: theme.textSecondary,
              margin: '0 0 0.25rem 0',
              textTransform: 'uppercase',
              letterSpacing: '0.05em'
            }}>
              {title}
            </h3>
            <div style={{
              fontSize: '1.5rem',
              fontWeight: '700',
              color: theme.text,
              lineHeight: 1,
              margin: 0
            }}>
              {value}
            </div>
          </div>
          
          <div style={{
            padding: '0.5rem',
            backgroundColor: `${cardColor}20`,
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            {React.cloneElement(icon, { size: 18, style: { color: cardColor } })}
          </div>
        </div>
        
        <div style={{
          fontSize: '0.75rem',
          color: theme.textSecondary,
          position: 'relative',
          zIndex: 1
        }}>
          {subtitle}
        </div>
      </div>
    );
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
          <p style={{ color: '#6b7280' }}>Loading city analysis...</p>
        </div>
      </div>
    );
  }

  // Financial Overview Component
  const FinancialOverview = ({ cityData }) => {
    const [viewMode, setViewMode] = useState('distribution');

    // Process financial data
    const incomeData = cityData.properties
      .filter(p => p.monthly_income && p.monthly_income > 0)
      .map(p => ({
        income: p.monthly_income,
        rooms: p.total_rooms,
        incomePerRoom: p.monthly_income / p.total_rooms,
        address: p.address
      }))
      .sort((a, b) => a.income - b.income);

    // Calculate statistics
    const stats = {
      totalProperties: cityData.properties.length,
      incomeProperties: incomeData.length,
      totalIncome: incomeData.reduce((sum, p) => sum + p.income, 0),
      averageIncome: incomeData.length > 0 ? incomeData.reduce((sum, p) => sum + p.income, 0) / incomeData.length : 0,
      medianIncome: incomeData.length > 0 ? incomeData[Math.floor(incomeData.length / 2)]?.income || 0 : 0,
      minIncome: incomeData.length > 0 ? incomeData[0]?.income || 0 : 0,
      maxIncome: incomeData.length > 0 ? incomeData[incomeData.length - 1]?.income || 0 : 0,
      averageIncomePerRoom: incomeData.length > 0 ?
        incomeData.reduce((sum, p) => sum + p.incomePerRoom, 0) / incomeData.length : 0
    };

    // Create distribution data (income ranges)
    // Helper function to create dynamic income ranges
    const createDynamicRanges = (incomeData, stats) => {
      if (!incomeData || incomeData.length === 0) {
        return [{ label: 'No Data', min: 0, max: Infinity }];
      }

      const { minIncome, maxIncome } = stats;
      const range = maxIncome - minIncome;
      
      // If all properties have the same income, create a single range
      if (range === 0) {
        return [{
          label: `£${Math.round(minIncome).toLocaleString()}`,
          min: minIncome - 0.1,
          max: minIncome + 0.1
        }];
      }
      
      // Determine number of buckets based on data size
      const dataSize = incomeData.length;
      let bucketCount;
      if (dataSize <= 5) bucketCount = Math.min(3, dataSize);
      else if (dataSize <= 15) bucketCount = 4;
      else if (dataSize <= 30) bucketCount = 5;
      else bucketCount = 6;
      
      // Calculate bucket size
      const bucketSize = range / bucketCount;
      
      // Create dynamic ranges
      const ranges = [];
      for (let i = 0; i < bucketCount; i++) {
        const min = minIncome + (i * bucketSize);
        const max = i === bucketCount - 1 ? maxIncome + 1 : minIncome + ((i + 1) * bucketSize);
        
        let label;
        if (i === bucketCount - 1) {
          // Last bucket: "£X+"
          label = `£${Math.round(min).toLocaleString()}+`;
        } else {
          // Regular buckets: "£X-£Y"
          label = `£${Math.round(min).toLocaleString()}-£${Math.round(max - 1).toLocaleString()}`;
        }
        
        ranges.push({ label, min, max });
      }
      
      return ranges;
    };

    // Create dynamic distribution data using the new function
    const ranges = createDynamicRanges(incomeData, stats);



    const distributionData = ranges.map(range => {
      const count = incomeData.filter(p => 
        p.income >= range.min && p.income < range.max
      ).length;
      return {
        label: range.label,
        count,
        percentage: incomeData.length > 0 ? (count / incomeData.length) * 100 : 0
      };
    });

    const viewTabs = [
      { key: 'distribution', label: 'Distribution' },
      { key: 'breakdown', label: 'Breakdown' },
      { key: 'comparison', label: 'Top Properties' }
    ];

    return (
      <div style={{
        backgroundColor: theme.cardBackground,
        borderRadius: '16px',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
        border: `1px solid ${theme.border}`,
        marginBottom: '2rem',
        transition: 'all 0.3s ease'
      }}>
        
        {/* Header */}
        <div style={{
          padding: '1.5rem',
          borderBottom: `1px solid ${theme.border}`
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '1rem'
          }}>
            <div>
              <h2 style={{
                fontSize: '1.25rem',
                fontWeight: '700',
                color: theme.text,
                margin: '0 0 0.25rem 0',
                letterSpacing: '-0.025em'
              }}>
                Financial Overview
              </h2>
              <p style={{
                fontSize: '0.875rem',
                color: theme.textSecondary,
                margin: 0
              }}>
                Revenue analysis and income distribution
              </p>
            </div>
          </div>

          {/* Tab Navigation - Matching your Analyze.jsx style */}
          <div style={{
            display: 'flex',
            borderBottom: `1px solid ${theme.border}`,
            overflowX: 'auto'
          }}>
            {viewTabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setViewMode(tab.key)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  padding: '1rem 1.5rem',
                  border: 'none',
                  backgroundColor: viewMode === tab.key ? currentPalette.primary : 'transparent',
                  color: viewMode === tab.key ? 'white' : theme.text,
                  fontSize: '0.875rem',
                  fontWeight: '500',
                  cursor: 'pointer',
                  borderBottom: viewMode === tab.key ? `2px solid ${currentPalette.primary}` : '2px solid transparent',
                  transition: 'all 0.2s ease',
                  whiteSpace: 'nowrap',
                  borderRadius: viewMode === tab.key ? '8px 8px 0 0' : '0'
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>


        {/* Content */}
        <div style={{ padding: '1.5rem' }}>
          {/* Key Stats Row */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: '16px',
            marginBottom: '24px'
          }}>
            <StatCard label="Total Income" value={`£${stats.totalIncome.toLocaleString()}`} subtitle="/month" />
            <StatCard label="Average Income" value={`£${Math.round(stats.averageIncome).toLocaleString()}`} subtitle="/property" />
            <StatCard label="Median Income" value={`£${Math.round(stats.medianIncome).toLocaleString()}`} subtitle="/property" />
            <StatCard label="Income per Room" value={`£${Math.round(stats.averageIncomePerRoom)}`} subtitle="/room/month" />
          </div>

          {/* Dynamic Content Based on View Mode */}
          {viewMode === 'distribution' && (
            <IncomeDistributionChart distributionData={distributionData} stats={stats} />
          )}
          
          {viewMode === 'breakdown' && (
            <IncomeBreakdown incomeData={incomeData} stats={stats} />
          )}
          
          {viewMode === 'comparison' && (
            <TopPropertiesTable incomeData={incomeData.slice(-10)} />
          )}
        </div>
      </div>
    );
  };


  if (error) {
    return (
      <div style={{
        minHeight: '100vh',
        backgroundColor: '#f9fafb',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <div style={{
          textAlign: 'center',
          padding: '24px',
          backgroundColor: 'white',
          borderRadius: '8px',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
        }}>
          <p style={{ color: '#dc2626', marginBottom: '16px' }}>{error}</p>
          <button
            onClick={handleBackToSelection}
            style={{
              padding: '8px 16px',
              backgroundColor: '#2563eb',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            Back to City Selection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: theme.background,
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      transition: 'all 0.3s ease'
    }}>
      {/* Professional Header */}
      <div style={{
        marginBottom: '2rem'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '1rem',
          marginBottom: '0.5rem'
        }}>
          <button
            onClick={handleBackToSelection}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.5rem 1rem',
              backgroundColor: theme.cardBg,
              border: `1px solid ${theme.border}`,
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '0.875rem',
              fontWeight: '500',
              color: theme.text,
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = currentPalette.primary;
              e.currentTarget.style.color = 'white';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = theme.cardBg;
              e.currentTarget.style.color = theme.text;
            }}
          >
            <ArrowLeft size={16} />
            Back to Cities
          </button>
        </div>
        
        <h1 style={{
          fontSize: '2rem',
          fontWeight: '700',
          color: theme.text,
          marginBottom: '0.5rem',
          letterSpacing: '-0.025em'
        }}>
          {capitalizeCityName(cityData.name)} Analysis
        </h1>
        <p style={{
          fontSize: '1rem',
          color: theme.textSecondary,
          margin: 0
        }}>
          Comprehensive analytics and market insights for {cityData.propertyCount} properties
        </p>
      </div>

      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '24px'
      }}>

        {/* Key Metrics Cards */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '24px',
          marginBottom: '32px'
        }}>
          <MetricCard 
            title="Total Properties" 
            value={cityData.propertyCount}
            subtitle={`${cityData.recentlyUpdated} updated recently`}
            icon={<BarChart3 style={{ width: '24px', height: '24px' }} />}
            color="blue"
            theme={theme}
          />
          <MetricCard 
            title="Monthly Income" 
            value={`£${cityData.totalIncome.toLocaleString()}`}
            subtitle={`£${cityData.avgIncome}/property avg`}
            icon={<TrendingUp style={{ width: '24px', height: '24px' }} />}
            color="green"
            theme={theme}  // ADD THIS
          />
          <MetricCard 
            title="Income Properties" 
            value={cityData.propertiesWithIncome}
            subtitle={`${Math.round((cityData.propertiesWithIncome / cityData.propertyCount) * 100)}% of total`}
            icon={<Clock style={{ width: '24px', height: '24px' }} />}
            color="orange"
            theme={theme}  // ADD THIS
          />
          <MetricCard 
            title="Areas Tracked" 
            value={cityData.areas.length}
            subtitle="Neighborhoods"
            icon={<BarChart3 style={{ width: '24px', height: '24px' }} />}
            color="purple"
            theme={theme}  // ADD THIS
          />
        </div>

        {/* Financial Overview Section */}
        <FinancialOverview cityData={cityData} />

        {/* Enhanced Income Distribution Section */}
        <EnhancedIncomeDistribution cityData={cityData} />

        {/* Market Timing Section */}
        <MarketTimingAnalysis cityData={cityData} />

        {/* Neighborhood Comparison Section */}
        <NeighborhoodComparison cityData={cityData} />

        {/* LTV Calculator Section */}
        <LTVCalculator cityData={cityData} />
      </div>
    </div>
  );
};

// Small stat card component
const StatCard = ({ label, value, subtitle }) => (
  <div style={{
    textAlign: 'center',
    padding: '12px',
    backgroundColor: '#f9fafb',
    borderRadius: '6px'
  }}>
    <div style={{
      fontSize: '1.25rem',
      fontWeight: 'bold',
      color: '#059669'
    }}>
      {value}
    </div>
    <div style={{
      fontSize: '12px',
      color: '#6b7280',
      fontWeight: '500'
    }}>
      {label}
    </div>
    {subtitle && (
      <div style={{
        fontSize: '11px',
        color: '#9ca3af'
      }}>
        {subtitle}
      </div>
    )}
  </div>
);

// Income Distribution Bar Chart
const IncomeDistributionChart = ({ distributionData, stats }) => {
  const maxCount = Math.max(...distributionData.map(d => d.count));
  
  // Calculate range info
  const getRangeInfo = () => {
    const dataSize = distributionData.reduce((sum, r) => sum + r.count, 0);
    const bucketCount = distributionData.length;
    return `${bucketCount} ranges • ${dataSize} properties`;
  };
  
  return (
    <div>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '16px'
      }}>
        <h3 style={{
          fontSize: '16px',
          fontWeight: '600',
          color: '#374151'
        }}>
          Income Distribution Analysis
        </h3>
        <div style={{
          fontSize: '12px',
          color: '#6b7280',
          backgroundColor: '#f9fafb',
          padding: '4px 8px',
          borderRadius: '4px'
        }}>
          {getRangeInfo()}
        </div>
      </div>
      
      <div style={{
        display: 'grid',
        gap: '12px'
      }}>
        {distributionData.map((range, index) => (
          <div key={range.label} style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}>
            <div style={{
              minWidth: '140px',
              fontSize: '14px',
              color: '#6b7280',
              fontWeight: '500'
            }}>
              {range.label}
            </div>
            <div style={{
              flex: 1,
              height: '24px',
              backgroundColor: '#f3f4f6',
              borderRadius: '12px',
              overflow: 'hidden',
              position: 'relative'
            }}>
              <div style={{
                height: '100%',
                width: `${maxCount > 0 ? (range.count / maxCount) * 100 : 0}%`,
                backgroundColor: '#059669',
                borderRadius: '12px',
                transition: 'width 0.5s ease'
              }} />
            </div>
            <div style={{
              width: '60px',
              fontSize: '14px',
              color: '#374151',
              fontWeight: '600',
              textAlign: 'right'
            }}>
              {range.count}
            </div>
            <div style={{
              width: '50px',
              fontSize: '12px',
              color: '#6b7280',
              textAlign: 'right'
            }}>
              {range.percentage.toFixed(1)}%
            </div>
          </div>
        ))}
      </div>
      
      {/* Summary stats */}
      <div style={{
        marginTop: '16px',
        padding: '12px',
        backgroundColor: '#f8fafc',
        borderRadius: '6px',
        fontSize: '12px',
        color: '#64748b'
      }}>
        <strong>Range:</strong> £{stats.minIncome.toLocaleString()} - £{stats.maxIncome.toLocaleString()} 
        <span style={{ margin: '0 12px' }}>•</span>
        <strong>Spread:</strong> £{(stats.maxIncome - stats.minIncome).toLocaleString()}
        <span style={{ margin: '0 12px' }}>•</span>
        <strong>Data Points:</strong> {distributionData.reduce((sum, r) => sum + r.count, 0)}
      </div>
    </div>
  );
};

// Income Breakdown
const IncomeBreakdown = ({ incomeData, stats }) => {
  return (
    <div>
      <h3 style={{
        fontSize: '16px',
        fontWeight: '600',
        color: '#374151',
        marginBottom: '16px'
      }}>
        Income Analysis Breakdown
      </h3>
      
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px'
      }}>
        <div style={{
          padding: '16px',
          backgroundColor: '#f0f9ff',
          borderRadius: '8px',
          border: '1px solid #0ea5e9'
        }}>
          <h4 style={{ color: '#0369a1', fontSize: '14px', fontWeight: '600', marginBottom: '8px' }}>
            Range Analysis
          </h4>
          <p style={{ fontSize: '12px', color: '#0369a1', marginBottom: '4px' }}>
            <strong>Highest:</strong> £{stats.maxIncome.toLocaleString()}
          </p>
          <p style={{ fontSize: '12px', color: '#0369a1', marginBottom: '4px' }}>
            <strong>Lowest:</strong> £{stats.minIncome.toLocaleString()}
          </p>
          <p style={{ fontSize: '12px', color: '#0369a1' }}>
            <strong>Spread:</strong> £{(stats.maxIncome - stats.minIncome).toLocaleString()}
          </p>
        </div>
        
        <div style={{
          padding: '16px',
          backgroundColor: '#f0fdf4',
          borderRadius: '8px',
          border: '1px solid #059669'
        }}>
          <h4 style={{ color: '#059669', fontSize: '14px', fontWeight: '600', marginBottom: '8px' }}>
            Per Room Metrics
          </h4>
          <p style={{ fontSize: '12px', color: '#059669', marginBottom: '4px' }}>
            <strong>Average:</strong> £{Math.round(stats.averageIncomePerRoom)}
          </p>
          <p style={{ fontSize: '12px', color: '#059669', marginBottom: '4px' }}>
            <strong>Total Rooms:</strong> {incomeData.reduce((sum, p) => sum + p.rooms, 0)}
          </p>
          <p style={{ fontSize: '12px', color: '#059669' }}>
            <strong>Avg per Property:</strong> {Math.round(incomeData.reduce((sum, p) => sum + p.rooms, 0) / incomeData.length)} rooms
          </p>
        </div>
      </div>
    </div>
  );
};

// Top Properties Table
const TopPropertiesTable = ({ incomeData }) => {
  return (
    <div>
      <h3 style={{
        fontSize: '16px',
        fontWeight: '600',
        color: '#374151',
        marginBottom: '16px'
      }}>
        Top Performing Properties
      </h3>
      
      <div style={{
        overflowX: 'auto'
      }}>
        <table style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: '14px'
        }}>
          <thead>
            <tr style={{ backgroundColor: '#f9fafb' }}>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#374151' }}>Address</th>
              <th style={{ padding: '12px', textAlign: 'right', fontWeight: '600', color: '#374151' }}>Rooms</th>
              <th style={{ padding: '12px', textAlign: 'right', fontWeight: '600', color: '#374151' }}>Monthly Income</th>
              <th style={{ padding: '12px', textAlign: 'right', fontWeight: '600', color: '#374151' }}>Per Room</th>
            </tr>
          </thead>
          <tbody>
            {incomeData.reverse().map((property, index) => (
              <tr key={index} style={{
                borderBottom: '1px solid #f3f4f6'
              }}>
                <td style={{ 
                  padding: '12px',
                  maxWidth: '200px',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap'
                }}>
                  {property.address}
                </td>
                <td style={{ padding: '12px', textAlign: 'right' }}>
                  {property.rooms}
                </td>
                <td style={{ 
                  padding: '12px', 
                  textAlign: 'right', 
                  color: '#059669', 
                  fontWeight: '600' 
                }}>
                  £{property.income.toLocaleString()}
                </td>
                <td style={{ padding: '12px', textAlign: 'right' }}>
                  £{Math.round(property.incomePerRoom)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// Reusable Analysis Section Component
const AnalysisSection = ({ title, icon, placeholder, features, isLast = false }) => {
  return (
    <div style={{
      backgroundColor: 'white',
      borderRadius: '8px',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
      border: '1px solid #e5e7eb',
      marginBottom: isLast ? '0' : '32px'
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
          alignItems: 'center'
        }}>
          {icon}
          {title}
        </h2>
      </div>
      <div style={{ padding: '24px' }}>
        <div style={{
          textAlign: 'center',
          color: '#6b7280',
          padding: '32px 0'
        }}>
          <div style={{
            width: '48px',
            height: '48px',
            margin: '0 auto 16px',
            opacity: 0.3
          }}>
            {React.cloneElement(icon, { 
              style: { width: '48px', height: '48px', color: '#d1d5db' }
            })}
          </div>
          <p style={{ marginBottom: '8px' }}>{placeholder}</p>
          <p style={{ fontSize: '14px', marginTop: '8px' }}>{features}</p>
        </div>
      </div>
    </div>
  );
};

// Neighborhood Comparison Component
const NeighborhoodComparison = ({ cityData }) => {
  const [selectedAreas, setSelectedAreas] = useState([]);
  const [comparisonData, setComparisonData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Process properties by area
  const propertiesByArea = useMemo(() => {
    const grouped = {};
    
    // Function to extract area from address if database area is missing
    const extractAreaFromAddress = (property) => {
      // First try database area field
      if (property.area && property.area.trim() !== '') {
        return property.area;
      }
      
      // Fallback: extract from address
      if (!property.address) return null; // Return null instead of 'Other'
      
      const addressParts = property.address.split(',').map(part => part.trim());
      
      // Known Oxford areas
      const oxfordAreas = ['Cowley', 'East Oxford', 'New Marston', 'Wood Farm', 'Cutteslowe', 'City Centre'];
      // Known Swindon areas  
      const swindonAreas = ['South Swindon', 'Kingshill'];
      // Known other areas
      const otherAreas = ['Ladygrove', 'Grimsbury', 'Kings End', 'Glory Farm'];
      
      const allKnownAreas = [...oxfordAreas, ...swindonAreas, ...otherAreas];
      
      // Look for known areas in address
      for (const part of addressParts) {
        for (const knownArea of allKnownAreas) {
          if (part.toLowerCase().includes(knownArea.toLowerCase())) {
            return knownArea;
          }
        }
      }
      
      // If no known area found, use the part before the city/postcode as area
      if (addressParts.length >= 2) {
        const potentialArea = addressParts[addressParts.length - 2];
        // Skip if it looks like a postcode or the city name
        if (!/^[A-Z]{1,2}[0-9]/.test(potentialArea) && 
            !potentialArea.toLowerCase().includes(cityData.name.toLowerCase())) {
          return potentialArea;
        }
      }
      
      return null; // Return null instead of 'Other'
    };
    
    cityData.properties.forEach(property => {
      const area = extractAreaFromAddress(property);
      if (area) { // Only group properties that have a valid area
        if (!grouped[area]) {
          grouped[area] = [];
        }
        grouped[area].push(property);
      }
    });
    
    return grouped;
  }, [cityData.properties, cityData.name]);

  // Calculate area metrics
  const areaMetrics = useMemo(() => {
    const metrics = {};
    
    Object.entries(propertiesByArea).forEach(([area, properties]) => {
      const propertiesWithIncome = properties.filter(p => p.monthly_income && p.monthly_income > 0);
      const totalIncome = propertiesWithIncome.reduce((sum, p) => sum + p.monthly_income, 0);
      const avgIncome = propertiesWithIncome.length > 0 ? totalIncome / propertiesWithIncome.length : 0;
      
      // Calculate average price per room
      const propertiesWithRooms = properties.filter(p => p.total_rooms && p.total_rooms > 0 && p.monthly_income && p.monthly_income > 0);
      const avgPricePerRoom = propertiesWithRooms.length > 0 ? 
        propertiesWithRooms.reduce((sum, p) => sum + (p.monthly_income / p.total_rooms), 0) / propertiesWithRooms.length : 0;

      // Calculate recently updated (last 30 days)
      const thirtyDaysAgo = new Date();
      thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
      const recentlyUpdated = properties.filter(p => 
        p.updated_at && new Date(p.updated_at) > thirtyDaysAgo
      ).length;

      metrics[area] = {
        totalProperties: properties.length,
        avgIncome: Math.round(avgIncome),
        totalIncome: Math.round(totalIncome),
        propertiesWithIncome: propertiesWithIncome.length,
        avgPricePerRoom: Math.round(avgPricePerRoom),
        recentlyUpdated,
        activityRate: properties.length > 0 ? Math.round((recentlyUpdated / properties.length) * 100) : 0
      };
    });
    
    return metrics;
  }, [propertiesByArea]);

  // Handle area selection
  const handleAreaToggle = (area) => {
    setSelectedAreas(prev => {
      if (prev.includes(area)) {
        return prev.filter(a => a !== area);
      } else if (prev.length < 4) { // Limit to 4 areas for readability
        return [...prev, area];
      }
      return prev;
    });
  };

  // Prepare comparison data
  const comparisonMetrics = useMemo(() => {
    if (selectedAreas.length === 0) return null;
    
    return selectedAreas.map(area => ({
      area,
      ...areaMetrics[area]
    }));
  }, [selectedAreas, areaMetrics]);

  const sortedAreas = useMemo(() => {
    return Object.keys(areaMetrics).sort((a, b) => {
      // Sort by total properties descending, then alphabetically
      const diffProperties = areaMetrics[b].totalProperties - areaMetrics[a].totalProperties;
      if (diffProperties !== 0) return diffProperties;
      return a.localeCompare(b);
    });
  }, [areaMetrics]);

  return (
    <div style={{
      backgroundColor: 'white',
      borderRadius: '8px',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
      border: '1px solid #e5e7eb',
      marginBottom: '0'
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
          marginBottom: '12px'
        }}>
          <MapPin style={{ width: '20px', height: '20px', marginRight: '8px', color: '#2563eb' }} />
          Neighborhood Comparison
        </h2>
        <p style={{
          fontSize: '14px',
          color: '#6b7280',
          marginBottom: '16px'
        }}>
          Select up to 4 areas to compare their performance metrics. Data includes property counts, income averages, and market activity.
        </p>

        {/* Area Selection */}
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '8px'
        }}>
          {sortedAreas.map(area => {
            const isSelected = selectedAreas.includes(area);
            const metrics = areaMetrics[area];
            
            return (
              <button
                key={area}
                onClick={() => handleAreaToggle(area)}
                disabled={!isSelected && selectedAreas.length >= 4}
                style={{
                  padding: '8px 12px',
                  borderRadius: '20px',
                  border: isSelected ? '2px solid #2563eb' : '1px solid #d1d5db',
                  backgroundColor: isSelected ? '#eff6ff' : 'white',
                  color: isSelected ? '#2563eb' : '#374151',
                  fontSize: '14px',
                  cursor: (!isSelected && selectedAreas.length >= 4) ? 'not-allowed' : 'pointer',
                  opacity: (!isSelected && selectedAreas.length >= 4) ? 0.5 : 1,
                  transition: 'all 0.2s'
                }}
              >
                {area}
              </button>
            );
          })}
        </div>

        {selectedAreas.length >= 4 && (
          <p style={{
            fontSize: '12px',
            color: '#f59e0b',
            marginTop: '8px',
            fontStyle: 'italic'
          }}>
            Maximum 4 areas selected for optimal comparison view
          </p>
        )}
      </div>

      <div style={{ padding: '24px' }}>
        {selectedAreas.length === 0 ? (
          <div style={{
            textAlign: 'center',
            color: '#6b7280',
            padding: '32px 0'
          }}>
            <MapPin style={{ 
              width: '48px', 
              height: '48px', 
              color: '#d1d5db',
              margin: '0 auto 16px'
            }} />
            <p style={{ marginBottom: '8px' }}>Select areas above to start comparing</p>
            <p style={{ fontSize: '14px' }}>
              Choose 2-4 neighborhoods to see side-by-side performance metrics
            </p>
          </div>
        ) : (
          <div>
            {/* Comparison Table */}
            <div style={{
              overflowX: 'auto',
              marginBottom: '24px'
            }}>
              <table style={{
                width: '100%',
                borderCollapse: 'collapse',
                fontSize: '14px'
              }}>
                <thead>
                  <tr style={{ backgroundColor: '#f9fafb' }}>
                    <th style={{
                      padding: '12px',
                      textAlign: 'left',
                      fontWeight: '600',
                      color: '#374151',
                      borderBottom: '2px solid #e5e7eb'
                    }}>
                      Area
                    </th>
                    <th style={{
                      padding: '12px',
                      textAlign: 'right',
                      fontWeight: '600',
                      color: '#374151',
                      borderBottom: '2px solid #e5e7eb'
                    }}>
                      Properties
                    </th>
                    <th style={{
                      padding: '12px',
                      textAlign: 'right',
                      fontWeight: '600',
                      color: '#374151',
                      borderBottom: '2px solid #e5e7eb'
                    }}>
                      Avg Income
                    </th>
                    <th style={{
                      padding: '12px',
                      textAlign: 'right',
                      fontWeight: '600',
                      color: '#374151',
                      borderBottom: '2px solid #e5e7eb'
                    }}>
                      Per Room
                    </th>
                    <th style={{
                      padding: '12px',
                      textAlign: 'right',
                      fontWeight: '600',
                      color: '#374151',
                      borderBottom: '2px solid #e5e7eb'
                    }}>
                      Activity
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {comparisonMetrics.map((area, index) => (
                    <tr key={area.area} style={{
                      borderBottom: index === comparisonMetrics.length - 1 ? 'none' : '1px solid #f3f4f6'
                    }}>
                      <td style={{
                        padding: '12px',
                        fontWeight: '500',
                        color: '#111827'
                      }}>
                        {area.area}
                      </td>
                      <td style={{
                        padding: '12px',
                        textAlign: 'right',
                        color: '#374151'
                      }}>
                        {area.totalProperties}
                      </td>
                      <td style={{
                        padding: '12px',
                        textAlign: 'right',
                        color: '#059669',
                        fontWeight: '600'
                      }}>
                        £{area.avgIncome.toLocaleString()}
                      </td>
                      <td style={{
                        padding: '12px',
                        textAlign: 'right',
                        color: '#374151'
                      }}>
                        £{area.avgPricePerRoom}
                      </td>
                      <td style={{
                        padding: '12px',
                        textAlign: 'right',
                        color: area.activityRate > 20 ? '#059669' : area.activityRate > 10 ? '#f59e0b' : '#6b7280'
                      }}>
                        {area.activityRate}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Performance Comparison Charts */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
              gap: '24px'
            }}>
              {/* Average Income Comparison */}
              <ComparisonChart
                title="Average Monthly Income"
                data={comparisonMetrics}
                valueKey="avgIncome"
                color="#059669"
                formatValue={(value) => `£${value.toLocaleString()}`}
              />

              {/* Per Room Comparison */}
              <ComparisonChart
                title="Average Per Room"
                data={comparisonMetrics}
                valueKey="avgPricePerRoom"
                color="#2563eb"
                formatValue={(value) => `£${value}`}
              />

              {/* Property Count Comparison */}
              <ComparisonChart
                title="Property Count"
                data={comparisonMetrics}
                valueKey="totalProperties"
                color="#7c3aed"
                formatValue={(value) => value.toString()}
              />

              {/* Activity Rate Comparison */}
              <ComparisonChart
                title="Recent Activity Rate"
                data={comparisonMetrics}
                valueKey="activityRate"
                color="#ea580c"
                formatValue={(value) => `${value}%`}
              />
            </div>

            {/* Key Insights */}
            <div style={{
              marginTop: '24px',
              padding: '16px',
              backgroundColor: '#f0f9ff',
              borderRadius: '8px',
              border: '1px solid #0ea5e9'
            }}>
              <h4 style={{
                fontSize: '16px',
                fontWeight: '600',
                color: '#0369a1',
                marginBottom: '8px'
              }}>
                Key Insights
              </h4>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '12px',
                fontSize: '14px',
                color: '#0369a1'
              }}>
                <div>
                  <strong>Highest Income:</strong> {comparisonMetrics.reduce((max, area) => 
                    area.avgIncome > max.avgIncome ? area : max
                  ).area} (£{comparisonMetrics.reduce((max, area) => 
                    area.avgIncome > max.avgIncome ? area : max
                  ).avgIncome.toLocaleString()})
                </div>
                <div>
                  <strong>Most Properties:</strong> {comparisonMetrics.reduce((max, area) => 
                    area.totalProperties > max.totalProperties ? area : max
                  ).area} ({comparisonMetrics.reduce((max, area) => 
                    area.totalProperties > max.totalProperties ? area : max
                  ).totalProperties})
                </div>
                <div>
                  <strong>Most Active:</strong> {comparisonMetrics.reduce((max, area) => 
                    area.activityRate > max.activityRate ? area : max
                  ).area} ({comparisonMetrics.reduce((max, area) => 
                    area.activityRate > max.activityRate ? area : max
                  ).activityRate}%)
                </div>
                <div>
                  <strong>Best Per Room:</strong> {comparisonMetrics.reduce((max, area) => 
                    area.avgPricePerRoom > max.avgPricePerRoom ? area : max
                  ).area} (£{comparisonMetrics.reduce((max, area) => 
                    area.avgPricePerRoom > max.avgPricePerRoom ? area : max
                  ).avgPricePerRoom})
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Simple comparison chart component
const ComparisonChart = ({ title, data, valueKey, color, formatValue }) => {
  const maxValue = Math.max(...data.map(item => item[valueKey]));
  
  return (
    <div style={{
      padding: '16px',
      backgroundColor: '#f9fafb',
      borderRadius: '8px',
      border: '1px solid #e5e7eb'
    }}>
      <h4 style={{
        fontSize: '14px',
        fontWeight: '600',
        color: '#374151',
        marginBottom: '12px'
      }}>
        {title}
      </h4>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {data.map((item, index) => {
          const value = item[valueKey];
          const percentage = maxValue > 0 ? (value / maxValue) * 100 : 0;
          
          return (
            <div key={item.area} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{
                fontSize: '12px',
                fontWeight: '500',
                color: '#6b7280',
                width: '80px',
                textAlign: 'right'
              }}>
                {item.area}
              </div>
              <div style={{
                flex: 1,
                height: '20px',
                backgroundColor: '#e5e7eb',
                borderRadius: '10px',
                overflow: 'hidden',
                position: 'relative'
              }}>
                <div style={{
                  height: '100%',
                  width: `${percentage}%`,
                  backgroundColor: color,
                  borderRadius: '10px',
                  transition: 'width 0.5s ease'
                }} />
              </div>
              <div style={{
                fontSize: '12px',
                fontWeight: '600',
                color: '#374151',
                width: '80px'
              }}>
                {formatValue(value)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default IndividualCityAnalysis;