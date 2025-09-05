import React from 'react';
import { BarChart3, TrendingUp, Home, Users, DollarSign, Calendar } from 'lucide-react';

const StatisticsSection = ({ 
  // Use the same data that History.jsx already has
  sortedProperties = [],
  selectedCity,
  selectedSuburb, 
  filterBy,
  theme,
  currentPalette,
  isDarkMode 
}) => {
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency: 'GBP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const formatPercentage = (percentage) => {
    return `${percentage}%`;
  };

  // Calculate statistics from the filtered properties data (same as History.jsx logic)
  const getFilteredStatsData = () => {
    const dataForStats = sortedProperties; // Already filtered by History.jsx
    
    const totalProperties = dataForStats.length;
    const viableProperties = dataForStats.filter(p => 
      p.meets_requirements?.toLowerCase().includes('yes')
    ).length;
    const totalIncome = dataForStats.reduce((sum, p) => 
      sum + (Number(p.monthly_income) || 0), 0
    );
    const updatedProperties = dataForStats.filter(p => p.has_updates).length;
    
    // Calculate monthly metrics
    const currentMonthStart = new Date();
    currentMonthStart.setDate(1);
    currentMonthStart.setHours(0, 0, 0, 0);
    
    const propertiesAddedThisMonth = dataForStats.filter(p => {
      if (!p.date_found && !p.analysis_date && !p.created_at) return false;
      const dateFound = new Date(p.date_found || p.analysis_date || p.created_at);
      return dateFound >= currentMonthStart;
    }).length;
    
    // Count rooms that went off market this month (from date_gone)
    const roomsOffMarket = dataForStats.reduce((sum, p) => {
      if (p.date_gone) {
        const dateGone = new Date(p.date_gone);
        if (dateGone >= currentMonthStart) {
          return sum + (p.total_rooms || 0);
        }
      }
      return sum;
    }, 0);
    
    return {
      totalProperties,
      viableProperties,
      totalIncome,
      updatedProperties,
      propertiesAddedThisMonth,
      roomsOffMarket
    };
  };

  const getLocationContext = () => {
    if (selectedCity === 'all') {
      return 'All Locations';
    } else if (selectedSuburb === 'all') {
      return selectedCity;
    } else {
      return `${selectedSuburb}, ${selectedCity}`;
    }
  };

  // Get the calculated statistics
  const {
    totalProperties,
    viableProperties,
    totalIncome,
    updatedProperties,
    propertiesAddedThisMonth,
    roomsOffMarket
  } = getFilteredStatsData();

  const locationContext = getLocationContext();
  const updatedPercentage = totalProperties > 0 ? Math.round((updatedProperties / totalProperties) * 100) : 0;

  const statCards = [
    {
      title: 'Total Properties',
      value: totalProperties,
      icon: Home,
      color: currentPalette.primary,
      subtitle: 'In your portfolio'
    },
    {
      title: 'Rooms Off Market', 
      value: roomsOffMarket,
      icon: TrendingUp,
      color: roomsOffMarket > 0 ? '#ef4444' : '#10b981',
      subtitle: 'Gone off market this month'
    },
    {
      title: 'Properties Added',
      value: propertiesAddedThisMonth,
      icon: DollarSign,
      color: '#059669',
      subtitle: 'Added this month'
    },
    {
      title: 'Recently Updated',
      value: updatedProperties,
      icon: Calendar,
      color: currentPalette.secondary,
      subtitle: `${formatPercentage(updatedPercentage)} of properties`
    }
  ];

  return (
    <div style={{
      backgroundColor: theme.cardBg,
      borderRadius: '12px',
      padding: '1.5rem',
      marginBottom: '1.5rem',
      border: `1px solid ${theme.border}`,
      boxShadow: '0 2px 10px rgba(0, 0, 0, 0.08)',
      transition: 'all 0.3s ease'
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
        marginBottom: '1.5rem',
        paddingBottom: '0.75rem',
        borderBottom: `1px solid ${theme.border}`
      }}>
        <div style={{
          padding: '0.375rem',
          backgroundColor: `rgba(${currentPalette.primary.slice(1).match(/.{2}/g).map(hex => parseInt(hex, 16)).join(', ')}, 0.1)`,
          borderRadius: '8px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <BarChart3 size={20} style={{ color: currentPalette.primary }} />
        </div>
        <div>
          <h2 style={{
            fontSize: '1.25rem',
            fontWeight: '600',
            color: theme.text,
            margin: 0,
            lineHeight: 1
          }}>
            📊 Statistics for {locationContext}
          </h2>
          <p style={{
            fontSize: '0.8rem',
            color: theme.textSecondary,
            margin: '2px 0 0 0'
          }}>
            Updated automatically based on your current filters
          </p>
        </div>
      </div>

      {/* Statistics Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '1rem'
      }}>
        {statCards.map((stat, index) => {
          const IconComponent = stat.icon;
          
          return (
            <div
              key={index}
              style={{
                padding: '1rem',
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
                e.currentTarget.style.borderColor = stat.color;
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
                background: `linear-gradient(135deg, ${stat.color}12, ${stat.color}03)`,
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
                    {stat.title}
                  </h3>
                  <div style={{
                    fontSize: '1.5rem',
                    fontWeight: '700',
                    color: theme.text,
                    lineHeight: 1,
                    margin: 0
                  }}>
                    {stat.value}
                  </div>
                </div>
                
                <div style={{
                  padding: '0.5rem',
                  backgroundColor: `${stat.color}20`,
                  borderRadius: '8px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <IconComponent size={18} style={{ color: stat.color }} />
                </div>
              </div>
              
              <div style={{
                fontSize: '0.75rem',
                color: theme.textSecondary,
                position: 'relative',
                zIndex: 1
              }}>
                {stat.subtitle}
              </div>
            </div>
          );
        })}
      </div>

      {/* Additional Info Bar */}
      <div style={{
        marginTop: '1rem',
        padding: '0.75rem',
        backgroundColor: isDarkMode ? 'rgba(255, 255, 255, 0.03)' : '#f1f5f9',
        borderRadius: '8px',
        border: `1px solid ${theme.border}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '0.375rem'
      }}>
        <div style={{
          width: '5px',
          height: '5px',
          backgroundColor: currentPalette.primary,
          borderRadius: '50%'
        }} />
        <span style={{
          fontSize: '0.8rem',
          color: theme.textSecondary,
          fontWeight: '500'
        }}>
          Filtered data • {totalProperties} properties shown
          {filterBy !== 'all' && ` • ${filterBy.replace('-', ' ')}`}
        </span>
      </div>

      <style jsx>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

// Example usage component showing how to integrate with History.jsx
const ExampleUsage = () => {
  // Mock the data structure that History.jsx already has
  const mockSortedProperties = [
    {
      property_id: '1',
      address: '123 Oxford Street, Oxford',
      meets_requirements: 'Yes - viable',
      monthly_income: 2500,
      has_updates: true,
      date_found: '2024-01-15',
      date_gone: null,
      total_rooms: 5
    },
    {
      property_id: '2', 
      address: '456 High Street, Banbury',
      meets_requirements: 'No - issues found',
      monthly_income: 1800,
      has_updates: false,
      date_found: '2024-02-01',
      date_gone: '2024-02-15',
      total_rooms: 4
    }
  ];

  const mockTheme = {
    cardBg: '#ffffff',
    border: 'rgba(168, 165, 160, 0.3)',
    text: '#2C3E4A',
    textSecondary: '#A8A5A0'
  };
  
  const mockPalette = {
    primary: '#667eea',
    secondary: '#764ba2'
  };

  return (
    <div style={{ 
      padding: '2rem', 
      backgroundColor: '#F5F1E8',
      minHeight: '100vh'
    }}>
      <StatisticsSection 
        sortedProperties={mockSortedProperties}
        selectedCity="Oxford"
        selectedSuburb="all"
        filterBy="all"
        theme={mockTheme}
        currentPalette={mockPalette}
        isDarkMode={false}
      />
      
      <div style={{
        marginTop: '1rem',
        padding: '1rem',
        backgroundColor: '#f8fafc',
        borderRadius: '8px',
        fontSize: '0.875rem'
      }}>
        <strong>Integration with History.jsx:</strong> Simply replace your existing statistics section with:
        <pre style={{ 
          marginTop: '0.5rem', 
          fontSize: '0.75rem', 
          backgroundColor: '#f1f5f9', 
          padding: '0.5rem', 
          borderRadius: '4px',
          overflow: 'auto'
        }}>
{`<StatisticsSection 
  sortedProperties={sortedProperties}  // Your existing filtered data
  selectedCity={selectedCity}          // Your existing state
  selectedSuburb={selectedSuburb}      // Your existing state  
  filterBy={filterBy}                  // Your existing state
  theme={theme}                        // Your existing theme
  currentPalette={currentPalette}      // Your existing palette
  isDarkMode={isDarkMode}              // Your existing dark mode
/>`}
        </pre>
        <p style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: '#64748b' }}>
          No API changes needed! Uses the same data and logic as your existing statistics.
        </p>
      </div>
    </div>
  );
};

export default StatisticsSection;