import React, { useState, useMemo } from 'react';
import { Calculator, TrendingUp, Home, Percent, ChevronDown, ChevronUp } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { useDarkMode } from '../contexts/DarkModeContext';

const LTVCalculator = ({ cityData }) => {
  // State for all the sliding inputs
  const [ltvPercentage, setLtvPercentage] = useState(75);
  const [costPercentage, setCostPercentage] = useState(15);
  const [rentalYield, setRentalYield] = useState(7);
  const [showRoomConfig, setShowRoomConfig] = useState(false);
  const [roomRange, setRoomRange] = useState({ min: 4, max: 10 });

  const { currentPalette } = useTheme();
  const { isDarkMode } = useDarkMode();

  const baseColors = {
    darkSlate: '#2C3E4A',
    lightCream: '#F5F1E8',
    softGray: '#A8A5A0',
  };

  const theme = isDarkMode ? {
    background: '#1a202c',
    cardBg: '#2d3748',
    text: baseColors.lightCream,
    textSecondary: '#a0aec0',
    border: 'rgba(255, 255, 255, 0.1)',
    accent: currentPalette.primary
  } : {
    background: '#f7fafc',
    cardBg: '#ffffff',
    text: baseColors.darkSlate,
    textSecondary: baseColors.softGray,
    border: '#e2e8f0',
    accent: currentPalette.primary
  };

  // Helper function to capitalize city name
  const capitalizeCityName = (name) => {
    if (!name) return 'City';
    return name.charAt(0).toUpperCase() + name.slice(1).toLowerCase();
  };

  // Calculate average rent per room from city data
  const averageRentPerRoom = useMemo(() => {
    if (!cityData?.properties) return 650; // Default fallback
    
    const propertiesWithIncome = cityData.properties.filter(p => 
      p.monthly_income && p.monthly_income > 0 && p.total_rooms && p.total_rooms > 0
    );
    
    if (propertiesWithIncome.length === 0) return 650;
    
    const totalRentPerRoom = propertiesWithIncome.reduce((sum, p) => 
      sum + (p.monthly_income / p.total_rooms), 0
    );
    
    return Math.round(totalRentPerRoom / propertiesWithIncome.length);
  }, [cityData]);

  // Generate room count array based on range
  const roomCounts = useMemo(() => {
    const rooms = [];
    for (let i = roomRange.min; i <= roomRange.max; i++) {
      rooms.push(i);
    }
    return rooms;
  }, [roomRange]);

  // Calculate property valuation using the formula
  const calculateValuation = (avgRent, rooms) => {
    // Formula: ((Average Rent per Room × Number of Rooms × 12) × (1 - Cost Percentage)) ÷ Rental Yield
    const annualRent = avgRent * rooms * 12;
    const netRent = annualRent * (1 - (costPercentage / 100));
    const valuation = netRent / (rentalYield / 100);
    return valuation;
  };

  // Calculate mortgage amount
  const calculateMortgage = (valuation) => {
    return valuation * (ltvPercentage / 100);
  };

  // Get calculations for different room counts
  const currentCalculations = useMemo(() => {
    return roomCounts.map(roomCount => {
      const valuation = calculateValuation(averageRentPerRoom, roomCount);
      const mortgage = calculateMortgage(valuation);
      return {
        rooms: roomCount,
        valuation,
        mortgage,
        totalRent: averageRentPerRoom * roomCount
      };
    });
  }, [ltvPercentage, costPercentage, rentalYield, averageRentPerRoom, roomCounts]);

  return (
    <div style={{
      backgroundColor: theme.cardBg,
      borderRadius: '16px',
      boxShadow: isDarkMode ? '0 4px 20px rgba(0, 0, 0, 0.3)' : '0 4px 20px rgba(0, 0, 0, 0.1)',
      border: `1px solid ${theme.border}`,
      marginBottom: '24px',
      transition: 'all 0.3s ease'
    }}>
      {/* Header */}
      <div style={{
        padding: '2rem',
        borderBottom: `1px solid ${theme.border}`
      }}>
        <h2 style={{
          fontSize: '1.5rem',
          fontWeight: '600',
          color: theme.text,
          display: 'flex',
          alignItems: 'center',
          marginBottom: '0.5rem'
        }}>
          <Calculator style={{ width: '24px', height: '24px', marginRight: '12px', color: currentPalette.primary }} />
          LTV Calculator
        </h2>
        <p style={{
          fontSize: '0.875rem',
          color: theme.textSecondary,
          margin: 0
        }}>
          Calculate property valuations and mortgage amounts for room share properties
        </p>
      </div>

      <div style={{ padding: '2rem' }}>
        {/* Input Controls */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '24px',
          marginBottom: '24px'
        }}>
          {/* LTV Percentage */}
          <div>
            <label style={{
              fontSize: '0.875rem',
              fontWeight: '600',
              color: theme.text,
              marginBottom: '12px',
              display: 'block'
            }}>
              LTV Percentage: {ltvPercentage}%
            </label>
            <input
              type="range"
              min="25"
              max="95"
              step="1"
              value={ltvPercentage}
              onChange={(e) => setLtvPercentage(Number(e.target.value))}
              style={{
                width: '100%',
                height: '6px',
                borderRadius: '3px',
                background: theme.border,
                outline: 'none',
                cursor: 'pointer',
                appearance: 'none'
              }}
            />
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: '12px',
              color: theme.textSecondary,
              marginTop: '8px'
            }}> 
              <span>25%</span>
              <span>95%</span>
            </div>
          </div>

          {/* Cost Percentage */}
          <div>
            <label style={{
              fontSize: '0.875rem',
              fontWeight: '600',
              color: theme.text,
              marginBottom: '12px',
              display: 'block'
            }}>
              Cost Percentage: {costPercentage}%
            </label>
            <input
              type="range"
              min="0"
              max="30"
              step="1"
              value={costPercentage}
              onChange={(e) => setCostPercentage(Number(e.target.value))}
              style={{
                width: '100%',
                height: '6px',
                borderRadius: '3px',
                background: theme.border,
                outline: 'none',
                cursor: 'pointer',
                appearance: 'none'
              }}
            />
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: '12px',
              color: theme.textSecondary,
              marginTop: '4px'
            }}>
              <span>0%</span>
              <span>30%</span>
            </div>
          </div>

          {/* Rental Yield */}
          <div>
            <label style={{
              fontSize: '0.875rem',
              fontWeight: '600',
              color: theme.text,
              marginBottom: '12px',
              display: 'block'
            }}>
              Rental Yield: {rentalYield.toFixed(1)}%
            </label>
            <input
              type="range"
              min="4"
              max="12"
              step="0.1"
              value={rentalYield}
              onChange={(e) => setRentalYield(Number(e.target.value))}
              style={{
                width: '100%',
                height: '6px',
                borderRadius: '3px',
                background: theme.border,
                outline: 'none',
                cursor: 'pointer',
                appearance: 'none'
              }}
            />
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: '12px',
              color: theme.textSecondary,
              marginTop: '4px'
            }}>
              <span>4.0%</span>
              <span>12.0%</span>
            </div>
          </div>
        </div>

        {/* Room Configuration Section (Collapsible) */}
        <div style={{
          marginBottom: '32px',
          border: `1px solid ${theme.border}`,
          borderRadius: '12px',
          overflow: 'hidden',
          backgroundColor: theme.cardBg
        }}>
          <button
            onClick={() => setShowRoomConfig(!showRoomConfig)}
            style={{
              width: '100%',
              padding: '16px',
              backgroundColor: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : '#f8fafc',
              border: 'none',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '600',
              color: theme.text
            }}
          >
            <span>Room Range Configuration (Currently: {roomRange.min}-{roomRange.max} rooms)</span>
            {showRoomConfig ? (
              <ChevronUp style={{ width: '16px', height: '16px' }} />
            ) : (
              <ChevronDown style={{ width: '16px', height: '16px' }} />
            )}
          </button>
          
          {showRoomConfig && (
            <div style={{
              padding: '16px',
              backgroundColor: theme.cardBg,
              borderTop: `1px solid ${theme.border}`
            }}>
              <p style={{
                fontSize: '12px',
                color: theme.textSecondary,
                marginBottom: '16px'
              }}>
                Adjust the range of room counts to show in the calculation table.
              </p>
              
              <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '16px'
              }}>
                {/* Minimum Rooms */}
                <div>
                  <label style={{
                    fontSize: '14px',
                    fontWeight: '600',
                    color: theme.text,
                    marginBottom: '8px',
                    display: 'block'
                  }}>
                    Minimum Rooms: {roomRange.min}
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="15"
                    step="1"
                    value={roomRange.min}
                    onChange={(e) => {
                      const newMin = Number(e.target.value);
                      setRoomRange(prev => ({
                        min: newMin,
                        max: Math.max(newMin, prev.max)
                      }));
                    }}
                    style={{
                      width: '100%',
                      height: '6px',
                      borderRadius: '3px',
                      background: '#e5e7eb',
                      outline: 'none',
                      cursor: 'pointer'
                    }}
                  />
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    fontSize: '12px',
                    color: theme.textSecondary,
                    marginTop: '4px'
                  }}>
                    <span>1</span>
                    <span>15</span>
                  </div>
                </div>

                {/* Maximum Rooms */}
                <div>
                  <label style={{
                    fontSize: '14px',
                    fontWeight: '600',
                    color: theme.text,
                    marginBottom: '8px',
                    display: 'block'
                  }}>
                    Maximum Rooms: {roomRange.max}
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="15"
                    step="1"
                    value={roomRange.max}
                    onChange={(e) => {
                      const newMax = Number(e.target.value);
                      setRoomRange(prev => ({
                        min: Math.min(prev.min, newMax),
                        max: newMax
                      }));
                    }}
                    style={{
                      width: '100%',
                      height: '6px',
                      borderRadius: '3px',
                      background: '#e5e7eb',
                      outline: 'none',
                      cursor: 'pointer'
                    }}
                  />
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    fontSize: '12px',
                    color: theme.textSecondary,
                    marginTop: '4px'
                  }}>
                    <span>1</span>
                    <span>15</span>
                  </div>
                </div>
              </div>

              {/* Reset Button */}
              <div style={{ marginTop: '16px', textAlign: 'center' }}>
                <button
                  onClick={() => setRoomRange({ min: 4, max: 10 })}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: isDarkMode ? 'rgba(255, 255, 255, 0.1)' : '#f3f4f6',
                    border: `1px solid ${theme.border}`,
                    borderRadius: '6px',
                    fontSize: '12px',
                    color: theme.text,
                    cursor: 'pointer'
                  }}
                >
                  Reset to Default (4-10 rooms)
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Results Table */}
        <div style={{
          overflowX: 'auto',
          border: `1px solid ${theme.border}`,
          borderRadius: '12px',
          backgroundColor: theme.cardBg
        }}>
          <h3 style={{
            fontSize: '16px',
            fontWeight: '600',
            color: theme.text,  // instead of '#374151'
            marginBottom: '16px',
            display: 'flex',
            alignItems: 'center'
          }}>
            <TrendingUp style={{ width: '16px', height: '16px', marginRight: '8px' }} />
            Calculation Results - Room Share Properties ({roomRange.min}-{roomRange.max} rooms)
          </h3>

          <div style={{ overflowX: 'auto' }}>
            <table style={{
              width: '100%',
              borderCollapse: 'collapse',
              fontSize: '14px'
            }}>
              <thead>
                <tr style={{ backgroundColor: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : '#f8fafc' }}>
                  <th style={{ padding: '16px', textAlign: 'left', fontWeight: '600', color: theme.text, fontSize: '0.875rem' }}>
                    Rooms
                  </th>
                  <th style={{ padding: '16px', textAlign: 'left', fontWeight: '600', color: theme.text, fontSize: '0.875rem' }}>
                    Monthly Rent
                  </th>
                  <th style={{ padding: '16px', textAlign: 'left', fontWeight: '600', color: theme.text, fontSize: '0.875rem' }}>
                    Annual Income
                  </th>
                  <th style={{ padding: '16px', textAlign: 'left', fontWeight: '600', color: theme.text, fontSize: '0.875rem' }}>
                    Property Valuation
                  </th>
                  <th style={{ padding: '16px', textAlign: 'left', fontWeight: '600', color: theme.text, fontSize: '0.875rem' }}>
                    {ltvPercentage}% Mortgage
                  </th>
                </tr>
              </thead>
              <tbody>
                {currentCalculations.map((calc, index) => (
                  <tr key={index} style={{
                    borderBottom: index === currentCalculations.length - 1 ? 'none' : '1px solid #f3f4f6'
                  }}>
                    <td style={{ 
                      padding: '16px', 
                      fontWeight: '500', 
                      color: theme.text,
                      borderTop: index > 0 ? `1px solid ${theme.border}` : 'none'
                    }}>
                      {calc.rooms} Rooms
                    </td>
                    <td style={{ 
                      padding: '16px', 
                      fontWeight: '500', 
                      color: theme.text,
                      borderTop: index > 0 ? `1px solid ${theme.border}` : 'none'
                    }}>
                      £{calc.totalRent.toLocaleString()}
                    </td>
                    <td style={{ 
                      padding: '16px', 
                      fontWeight: '500', 
                      color: theme.text,
                      borderTop: index > 0 ? `1px solid ${theme.border}` : 'none'
                    }}>
                      £{(calc.totalRent * 12).toLocaleString()}
                    </td>
                    <td style={{ 
                      padding: '16px', 
                      fontWeight: '500', 
                      color: theme.text,
                      borderTop: index > 0 ? `1px solid ${theme.border}` : 'none'
                    }}>
                      £{Math.round(calc.valuation).toLocaleString()}
                    </td>
                    <td style={{
                      padding: '16px',
                      textAlign: 'right',
                      color: '#2563eb',
                      fontWeight: '600',
                      borderTop: index > 0 ? `1px solid ${theme.border}` : 'none'  // ADD this line
                    }}>
                      £{Math.round(calc.mortgage).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Key Metrics Summary */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px',
          marginTop: '24px'
        }}>
          <div style={{
            padding: '1.5rem',
            backgroundColor: isDarkMode ? 'rgba(59, 130, 246, 0.1)' : '#eff6ff',
            borderRadius: '12px',
            border: `1px solid ${isDarkMode ? 'rgba(59, 130, 246, 0.2)' : '#0ea5e9'}`,
            transition: 'all 0.3s ease'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              marginBottom: '8px'
            }}>
              <Home style={{ width: '16px', height: '16px', color: '#0369a1', marginRight: '8px' }} />
              <h4 style={{ fontSize: '14px', fontWeight: '600', color: '#0369a1' }}>
                Current Settings
              </h4>
            </div>
            <p style={{ fontSize: '12px', color: '#0369a1', marginBottom: '4px' }}>
              <strong>LTV:</strong> {ltvPercentage}%
            </p>
            <p style={{ fontSize: '12px', color: '#0369a1', marginBottom: '4px' }}>
              <strong>Costs:</strong> {costPercentage}%
            </p>
            <p style={{ fontSize: '12px', color: '#0369a1' }}>
              <strong>Yield:</strong> {rentalYield.toFixed(1)}%
            </p>
          </div>

          <div style={{
            padding: '1.5rem',
            backgroundColor: isDarkMode ? 'rgba(5, 150, 105, 0.1)' : '#f0fdf4',
            borderRadius: '12px',
            border: `1px solid ${isDarkMode ? 'rgba(5, 150, 105, 0.2)' : '#059669'}`,
            transition: 'all 0.3s ease'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              marginBottom: '8px'
            }}>
              <Percent style={{ width: '16px', height: '16px', color: '#059669', marginRight: '8px' }} />
              <h4 style={{ fontSize: '14px', fontWeight: '600', color: '#059669' }}>
                {capitalizeCityName(cityData?.name)} Data
              </h4>
            </div>
            <p style={{ fontSize: '12px', color: '#059669', marginBottom: '4px' }}>
              <strong>Avg Rent/Room:</strong> £{averageRentPerRoom}
            </p>
            <p style={{ fontSize: '12px', color: '#059669', marginBottom: '4px' }}>
              <strong>Properties:</strong> {cityData?.propertyCount || 0}
            </p>
            <p style={{ fontSize: '12px', color: '#059669' }}>
              <strong>Type:</strong> Room Share Properties
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LTVCalculator;