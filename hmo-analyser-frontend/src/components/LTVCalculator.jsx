import React, { useState, useMemo } from 'react';
import { Calculator, TrendingUp, Home, Percent, ChevronDown, ChevronUp } from 'lucide-react';

const LTVCalculator = ({ cityData }) => {
  // State for all the sliding inputs
  const [ltvPercentage, setLtvPercentage] = useState(75);
  const [costPercentage, setCostPercentage] = useState(15);
  const [rentalYield, setRentalYield] = useState(7);
  const [showRoomConfig, setShowRoomConfig] = useState(false);
  const [roomRange, setRoomRange] = useState({ min: 4, max: 10 });

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
      backgroundColor: 'white',
      borderRadius: '8px',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
      border: '1px solid #e5e7eb',
      marginBottom: '0',
      marginTop: '32px'
    }}>
      {/* Header */}
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
          <Calculator style={{ width: '20px', height: '20px', marginRight: '8px', color: '#059669' }} />
          LTV Calculator
        </h2>
        <p style={{
          fontSize: '14px',
          color: '#6b7280'
        }}>
          Calculate property valuations and mortgage amounts for room share properties. 
          Formula: ((Rent × Rooms × 12) × (1 - Costs)) ÷ Yield
        </p>
      </div>

      <div style={{ padding: '24px' }}>
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
              fontSize: '14px',
              fontWeight: '600',
              color: '#374151',
              marginBottom: '8px',
              display: 'block'
            }}>
              LTV Percentage: {ltvPercentage}%
            </label>
            <input
              type="range"
              min="50"
              max="95"
              step="1"
              value={ltvPercentage}
              onChange={(e) => setLtvPercentage(Number(e.target.value))}
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
              color: '#6b7280',
              marginTop: '4px'
            }}>
              <span>50%</span>
              <span>95%</span>
            </div>
          </div>

          {/* Cost Percentage */}
          <div>
            <label style={{
              fontSize: '14px',
              fontWeight: '600',
              color: '#374151',
              marginBottom: '8px',
              display: 'block'
            }}>
              Cost Percentage: {costPercentage}%
            </label>
            <input
              type="range"
              min="10"
              max="30"
              step="2.5"
              value={costPercentage}
              onChange={(e) => setCostPercentage(Number(e.target.value))}
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
              color: '#6b7280',
              marginTop: '4px'
            }}>
              <span>10%</span>
              <span>30%</span>
            </div>
          </div>

          {/* Rental Yield */}
          <div>
            <label style={{
              fontSize: '14px',
              fontWeight: '600',
              color: '#374151',
              marginBottom: '8px',
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
                background: '#e5e7eb',
                outline: 'none',
                cursor: 'pointer'
              }}
            />
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: '12px',
              color: '#6b7280',
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
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          overflow: 'hidden'
        }}>
          <button
            onClick={() => setShowRoomConfig(!showRoomConfig)}
            style={{
              width: '100%',
              padding: '16px',
              backgroundColor: '#f9fafb',
              border: 'none',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '600',
              color: '#374151'
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
              backgroundColor: 'white',
              borderTop: '1px solid #e5e7eb'
            }}>
              <p style={{
                fontSize: '12px',
                color: '#6b7280',
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
                    color: '#374151',
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
                    color: '#6b7280',
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
                    color: '#374151',
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
                    color: '#6b7280',
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
                    backgroundColor: '#f3f4f6',
                    border: '1px solid #d1d5db',
                    borderRadius: '6px',
                    fontSize: '12px',
                    color: '#374151',
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
          backgroundColor: '#f9fafb',
          borderRadius: '8px',
          padding: '16px',
          border: '1px solid #e5e7eb'
        }}>
          <h3 style={{
            fontSize: '16px',
            fontWeight: '600',
            color: '#374151',
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
                <tr style={{ backgroundColor: 'white' }}>
                  <th style={{
                    padding: '12px',
                    textAlign: 'left',
                    fontWeight: '600',
                    color: '#374151',
                    borderBottom: '2px solid #e5e7eb'
                  }}>
                    Rooms
                  </th>
                  <th style={{
                    padding: '12px',
                    textAlign: 'right',
                    fontWeight: '600',
                    color: '#374151',
                    borderBottom: '2px solid #e5e7eb'
                  }}>
                    Monthly Rent
                  </th>
                  <th style={{
                    padding: '12px',
                    textAlign: 'right',
                    fontWeight: '600',
                    color: '#374151',
                    borderBottom: '2px solid #e5e7eb'
                  }}>
                    Annual Income
                  </th>
                  <th style={{
                    padding: '12px',
                    textAlign: 'right',
                    fontWeight: '600',
                    color: '#374151',
                    borderBottom: '2px solid #e5e7eb'
                  }}>
                    Property Valuation
                  </th>
                  <th style={{
                    padding: '12px',
                    textAlign: 'right',
                    fontWeight: '600',
                    color: '#374151',
                    borderBottom: '2px solid #e5e7eb'
                  }}>
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
                      padding: '12px',
                      fontWeight: '500',
                      color: '#111827'
                    }}>
                      {calc.rooms} Rooms
                    </td>
                    <td style={{
                      padding: '12px',
                      textAlign: 'right',
                      color: '#374151'
                    }}>
                      £{calc.totalRent.toLocaleString()}
                    </td>
                    <td style={{
                      padding: '12px',
                      textAlign: 'right',
                      color: '#374151'
                    }}>
                      £{(calc.totalRent * 12).toLocaleString()}
                    </td>
                    <td style={{
                      padding: '12px',
                      textAlign: 'right',
                      color: '#059669',
                      fontWeight: '600'
                    }}>
                      £{Math.round(calc.valuation).toLocaleString()}
                    </td>
                    <td style={{
                      padding: '12px',
                      textAlign: 'right',
                      color: '#2563eb',
                      fontWeight: '600'
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
            padding: '16px',
            backgroundColor: '#f0f9ff',
            borderRadius: '8px',
            border: '1px solid #0ea5e9'
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
            padding: '16px',
            backgroundColor: '#f0fdf4',
            borderRadius: '8px',
            border: '1px solid #059669'
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