import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Calculator, TrendingUp, Home, Percent, ChevronDown, ChevronUp, DollarSign, PieChart } from 'lucide-react';
import LTVCalculator from '../components/LTVCalculator';
import { useTheme } from '../contexts/ThemeContext';
import { useDarkMode } from '../contexts/DarkModeContext';
import BRRRCalculator from '../components/brrrCalculator';

const DealCalculatorPage = () => {
  const [selectedCity, setSelectedCity] = useState('Oxford'); // Note: capital O
  const [ activeTab, setActiveTab ] = useState('deal-calculator');
  const { currentPalette } = useTheme();
  const { isDarkMode } = useDarkMode();
  
  const baseColors = {
    darkSlate: '#2C3E4A',
    lightCream: '#F5F1E8',
    softGray: '#A8A5A0',
  };

  const theme = isDarkMode ? {
    sidebarBg: `linear-gradient(180deg, ${baseColors.darkSlate} 0%, #1e3a47 100%)`,
    mainBg: '#1a2b32',
    cardBg: '#2c3e4a',
    text: baseColors.lightCream,
    textSecondary: currentPalette.secondary,
    border: 'rgba(180, 180, 180, 0.2)',
    accent: currentPalette.primary,
  } : {
    sidebarBg: `linear-gradient(180deg, ${currentPalette.primary} 0%, ${currentPalette.secondary} 100%)`,
    mainBg: baseColors.lightCream,
    cardBg: '#ffffff',
    text: baseColors.darkSlate,
    textSecondary: baseColors.softGray,
    border: 'rgba(168, 165, 160, 0.3)',
    accent: currentPalette.accent,
  };

  // Fetch available cities (same as IndividualCityAnalysis)
  const { data: availableCities = [] } = useQuery({
    queryKey: ['cities'],
    queryFn: async () => {
      const response = await fetch('/api/filters/cities');
      const data = await response.json();
      return data.cities || [];
    }
  });

  // Fetch ALL properties and filter by city (same as IndividualCityAnalysis)
  const { data: allProperties = [] } = useQuery({
    queryKey: ['properties'],
    queryFn: async () => {
      const response = await fetch('/api/properties?limit=10000');
      const data = await response.json();
      return Array.isArray(data) ? data : data.properties || [];
    }
  });

  // Filter properties for selected city (same logic as IndividualCityAnalysis)
  const currentCityData = useMemo(() => {
    if (!selectedCity || !allProperties.length) return null;

    const extractCityFromAddress = (address) => {
      if (!address) return null;
      const addressParts = address.split(',').map(part => part.trim());
      
      for (const part of addressParts) {
        if (part.toLowerCase() === selectedCity.toLowerCase()) {
          return selectedCity;
        }
      }
      return null;
    };

    const cityProperties = allProperties.filter(property => {
      const propertyCity = extractCityFromAddress(property.address);
      return propertyCity === selectedCity;
    });

    return {
      name: selectedCity,
      properties: cityProperties,
      propertyCount: cityProperties.length
    };
  }, [selectedCity, allProperties]);


  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: theme.mainBg,
      padding: '24px'
    }}>
      <div style={{
        maxWidth: '1400px',
        margin: '0 auto'
      }}>
        {/* Header */}
        <div style={{
          marginBottom: '32px',
          textAlign: 'center'
        }}>
          <h1 style={{
            fontSize: '2.5rem',
            fontWeight: 'bold',
            color: theme.text,
            marginBottom: '8px'
          }}>
            Deal Calculator
          </h1>
          <p style={{
            fontSize: '18px',
            color: theme.textSecondary
          }}>
            Calculate your property investment returns and cash requirements
          </p>
        </div>

                {/* City Selection */}
        <div style={{
          backgroundColor: theme.cardBg,
          borderRadius: '8px',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
          border: `1px solid ${theme.border}`,
          padding: '24px',
          marginBottom: '24px'
        }}>
          <h2 style={{
            fontSize: '1.25rem',
            fontWeight: '600',
            color: theme.text,
            marginBottom: '16px'
          }}>
            Select City
          </h2>
          <select
            value={selectedCity}
            onChange={(e) => setSelectedCity(e.target.value)}
            style={{
              width: '300px',
              padding: '12px',
              border: `1px solid ${theme.border}`,
              borderRadius: '6px',
              fontSize: '16px',
              backgroundColor: theme.cardBg,
              color: theme.text,
            }}
          >
            {availableCities.map((city) => (
              <option key={city} value={city}>
                {city}
              </option>
            ))}
          </select>
        </div>

        {/* ADD THIS TAB NAVIGATION SECTION HERE */}
        <div style={{
          backgroundColor: theme.cardBg,
          borderRadius: '8px',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
          border: `1px solid ${theme.border}`,
          marginBottom: '24px'
        }}>
          {/* Tab Navigation */}
          <div style={{
            display: 'flex',
            borderBottom: `1px solid ${theme.border}`
          }}>
            <button
              onClick={() => setActiveTab('deal-calculator')}
              style={{
                flex: 1,
                padding: '16px 24px',
                border: 'none',
                backgroundColor: activeTab === 'deal-calculator' ? theme.accent : 'transparent',
                color: activeTab === 'deal-calculator' ? 'white' : theme.text,
                fontSize: '16px',
                fontWeight: '600',
                cursor: 'pointer',
                borderRadius: activeTab === 'deal-calculator' ? '8px 0 0 0' : '0',
                transition: 'all 0.3s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px'
              }}
            >
              <DollarSign style={{ width: '20px', height: '20px' }} />
              Deal Calculator
            </button>
            <button
              onClick={() => setActiveTab('brrr-calculator')}
              style={{
                flex: 1,
                padding: '16px 24px',
                border: 'none',
                backgroundColor: activeTab === 'brrr-calculator' ? theme.accent : 'transparent',
                color: activeTab === 'brrr-calculator' ? 'white' : theme.text,
                fontSize: '16px',
                fontWeight: '600',
                cursor: 'pointer',
                borderRadius: activeTab === 'brrr-calculator' ? '0 8px 0 0' : '0',
                transition: 'all 0.3s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px'
              }}
            >
              <Calculator style={{ width: '20px', height: '20px' }} />
              BRRR Calculator
            </button>
          </div>

          {/* Tab Content Header */}
          <div style={{ padding: '24px' }}>
            {activeTab === 'deal-calculator' && (
              <>
                <h2 style={{
                  fontSize: '1.25rem',
                  fontWeight: '600',
                  color: theme.text,
                  display: 'flex',
                  alignItems: 'center',
                  marginBottom: '12px'
                }}>
                  <DollarSign style={{ width: '20px', height: '20px', marginRight: '8px', color: '#059669' }} />
                  Deal Calculator
                </h2>
                <p style={{
                  fontSize: '14px',
                  color: theme.textSecondary,
                }}>
                  Calculate your cash investment and monthly returns
                </p>
              </>
            )}
            {activeTab === 'brrr-calculator' && (
              <>
                <h2 style={{
                  fontSize: '1.25rem',
                  fontWeight: '600',
                  color: theme.text,
                  display: 'flex',
                  alignItems: 'center',
                  marginBottom: '12px'
                }}>
                  <Calculator style={{ width: '20px', height: '20px', marginRight: '8px', color: '#059669' }} />
                  BRRR Calculator
                </h2>
                <p style={{
                  fontSize: '14px',
                  color: theme.textSecondary,
                }}>
                  Buy, Refurbish, Rent, Refinance - Complete Deal Analysis
                </p>
              </>
            )}
          </div>
        </div>
        
        {/* Tab Content*/}

        {/* LTV Calculator */}
          {activeTab === 'deal-calculator' && (
            <>
            <LTVCalculator cityData={currentCityData} theme={theme} />

            {/* Deal Calculator */}
            <DealCalculator cityData={currentCityData} theme={theme} />
            </>
          )}
        
        {activeTab === 'brrr-calculator' && (
          <BRRRCalculator theme={theme} />
        )}
      </div>
    </div>
  );
};

// Deal Calculator Component
const DealCalculator = ({ cityData, theme }) => {
  // Deal Calculator State
  const [purchasePrice, setPurchasePrice] = useState(200000);
  const [costPerRoom, setCostPerRoom] = useState(25000);
  const [interestRate, setInterestRate] = useState(5.5);
  const [rentPerRoom, setRentPerRoom] = useState(500);
  const [numberOfRooms, setNumberOfRooms] = useState(5);
  const [mortgageTerm, setMortgageTerm] = useState(25);
  const [mortgageType, setMortgageType] = useState('repayment');
  const [depositPercentage, setDepositPercentage] = useState(25);
  const [ltvPercentage, setLtvPercentage] = useState(75);
  const [usingBridgingLoan, setUsingBridgingLoan] = useState(false);


  // Calculate average rent from city data as default
  const averageRentPerRoom = useMemo(() => {
    if (!cityData?.properties) return 500;
    
    const propertiesWithIncome = cityData.properties.filter(p => 
      p.monthly_income && p.monthly_income > 0 && p.total_rooms && p.total_rooms > 0
    );
    
    if (propertiesWithIncome.length === 0) return 500;
    
    const totalRentPerRoom = propertiesWithIncome.reduce((sum, p) => 
      sum + (p.monthly_income / p.total_rooms), 0
    );
    
    return Math.round(totalRentPerRoom / propertiesWithIncome.length);
  }, [cityData]);

  // Update default rent when city changes
  React.useEffect(() => {
    setRentPerRoom(averageRentPerRoom);
  }, [averageRentPerRoom]);

  // Calculations
  const calculations = useMemo(() => {
    // Total renovation costs
    const totalRenovationCosts = costPerRoom * numberOfRooms;
    
    // Total property cost
    const totalPropertyCost = purchasePrice + totalRenovationCosts;
    
    // Mortgage amount (from LTV)
    const mortgageAmount = purchasePrice * (ltvPercentage / 100);
    
    // Money in calculation: (Purchase Price + Renovation Costs) - Mortgage Amount
    const moneyIn = totalPropertyCost - mortgageAmount;
    
    // Monthly mortgage payment calculation
    const monthlyInterestRate = (interestRate / 100) / 12;
    const totalPayments = mortgageTerm * 12;

    let monthlyMortgagePayment;
    if (mortgageType === 'interest-only') {
    // Interest-only: just pay the monthly interest
    monthlyMortgagePayment = mortgageAmount * monthlyInterestRate;
    } else {
    // Repayment mortgage: pay both principal and interest
    monthlyMortgagePayment = mortgageAmount * 
        (monthlyInterestRate * Math.pow(1 + monthlyInterestRate, totalPayments)) / 
        (Math.pow(1 + monthlyInterestRate, totalPayments) - 1);
    }
    
    // Monthly income
    const monthlyRentIncome = rentPerRoom * numberOfRooms;
    
    // Monthly profit (before other costs)
    const monthlyProfit = monthlyRentIncome - monthlyMortgagePayment;
    
    // Annual figures
    const annualRentIncome = monthlyRentIncome * 12;
    const annualMortgagePayments = monthlyMortgagePayment * 12;
    const annualProfit = monthlyProfit * 12;
    
    // ROI calculations
    const roiPercentage = moneyIn > 0 ? (annualProfit / moneyIn) * 100 : 0;
    const monthlyRoiPercentage = roiPercentage / 12;

    // NEW: Required valuation to take all money out
    const requiredValuation = totalPropertyCost / (ltvPercentage / 100);

    // Deposit amount
    const depositAmount = purchasePrice * (depositPercentage / 100);

    // Bridge Amount
    const bridgePercentage = usingBridgingLoan ? Math.max(0, 100 - depositPercentage) : 0;
    const bridgeAmount = usingBridgingLoan ? purchasePrice * (bridgePercentage / 100) : 0;

    // Term Mortgage
    const termMortgageAmount = requiredValuation * (ltvPercentage / 100);
    
    return {
      totalRenovationCosts,
      totalPropertyCost,
      mortgageAmount,
      moneyIn,
      monthlyMortgagePayment,
      monthlyRentIncome,
      monthlyProfit,
      annualRentIncome,
      annualMortgagePayments,
      annualProfit,
      roiPercentage,
      monthlyRoiPercentage,
      depositAmount: usingBridgingLoan ? depositAmount: 0,
      requiredValuation,
      bridgeAmount,
      bridgePercentage,
      usingBridgingLoan,
      termMortgageAmount
    };
}, [purchasePrice, costPerRoom, numberOfRooms, ltvPercentage, depositPercentage, interestRate, rentPerRoom, mortgageTerm, mortgageType, usingBridgingLoan]);

  return (
    <div style={{
      backgroundColor: theme.cardBg,
      borderRadius: '8px',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
      border: `1px solid ${theme.border}`
    }}>
      <div style={{
        padding: '24px',
        borderBottom: `1px solid ${theme.border}`
      }}>
        <h2 style={{
          fontSize: '1.25rem',
          fontWeight: '600',
          color: theme.text,
          display: 'flex',
          alignItems: 'center',
          marginBottom: '12px'
        }}>
          <DollarSign style={{ width: '20px', height: '20px', marginRight: '8px', color: '#059669' }} />
          Deal Calculator
        </h2>
        <p style={{
          fontSize: '14px',
          color: theme.textSecondary,
        }}>
          Calculate your cash investment and monthly returns
        </p>
      </div>

      <div style={{ padding: '24px' }}>
        {/* Input Controls */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '24px',
          marginBottom: '32px'
        }}>
          {/* Purchase Price */}
          <div>
            <label style={{
              fontSize: '14px',
              fontWeight: '600',
              color: theme.text,
              marginBottom: '8px',
              display: 'block'
            }}>
              Purchase Price: £{purchasePrice.toLocaleString()}
            </label>
            <input
              type="range"
              min="50000"
              max="500000"
              step="5000"
              value={purchasePrice}
              onChange={(e) => setPurchasePrice(Number(e.target.value))}
              style={{
                width: '100%',
                height: '6px',
                borderRadius: '3px',
                background: theme.border,
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
              <span>£50k</span>
              <span>£500k</span>
            </div>
          </div>

          {/* Cost Per Room */}
          <div>
            <label style={{
              fontSize: '14px',
              fontWeight: '600',
              color: theme.text,
              marginBottom: '8px',
              display: 'block'
            }}>
              Cost Per Room: £{costPerRoom.toLocaleString()}
            </label>
            <input
              type="range"
              min="10000"
              max="50000"
              step="1000"
              value={costPerRoom}
              onChange={(e) => setCostPerRoom(Number(e.target.value))}
              style={{
                width: '100%',
                height: '6px',
                borderRadius: '3px',
                background: theme.border,
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
              <span>£10k</span>
              <span>£50k</span>
            </div>
          </div>

          {/* Interest Rate */}
          <div>
            <label style={{
              fontSize: '14px',
              fontWeight: '600',
              color: theme.text,
              marginBottom: '8px',
              display: 'block'
            }}>
              Interest Rate: {interestRate}%
            </label>
            <input
              type="range"
              min="2"
              max="15"
              step="0.1"
              value={interestRate}
              onChange={(e) => setInterestRate(Number(e.target.value))}
              style={{
                width: '100%',
                height: '6px',
                borderRadius: '3px',
                background: theme.border,
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
              <span>2%</span>
              <span>15%</span>
            </div>
          </div>

          {/* Rent Per Room */}
          <div>
            <label style={{
              fontSize: '14px',
              fontWeight: '600',
              color: theme.text,
              marginBottom: '8px',
              display: 'block'
            }}>
              Rent Per Room: £{rentPerRoom}/month
            </label>
            <input
              type="range"
              min="400"
              max="1500"
              step="25"
              value={rentPerRoom}
              onChange={(e) => setRentPerRoom(Number(e.target.value))}
              style={{
                width: '100%',
                height: '6px',
                borderRadius: '3px',
                background: theme.border,
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
              <span>£400</span>
              <span>£1,500</span>
            </div>
          </div>

          {/* Number of Rooms */}
          <div>
            <label style={{
              fontSize: '14px',
              fontWeight: '600',
              color: theme.text,
              marginBottom: '8px',
              display: 'block'
            }}>
              Number of Rooms: {numberOfRooms}
            </label>
            <input
              type="range"
              min="3"
              max="15"
              step="1"
              value={numberOfRooms}
              onChange={(e) => setNumberOfRooms(Number(e.target.value))}
              style={{
                width: '100%',
                height: '6px',
                borderRadius: '3px',
                background: theme.border,
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
              <span>3</span>
              <span>15</span>
            </div>
          </div>

          {/* Mortgage Term */}
          <div>
            <label style={{
              fontSize: '14px',
              fontWeight: '600',
              color: theme.text,
              marginBottom: '8px',
              display: 'block'
            }}>
              Mortgage Term: {mortgageTerm} years
            </label>
            <input
              type="range"
              min="15"
              max="35"
              step="1"
              value={mortgageTerm}
              onChange={(e) => setMortgageTerm(Number(e.target.value))}
              style={{
                width: '100%',
                height: '6px',
                borderRadius: '3px',
                background: theme.border,
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
              <span>15 years</span>
              <span>35 years</span>
            </div>
          </div>
          {/* LTV Percentage */}
            <div>
            <label style={{
                fontSize: '14px',
                fontWeight: '600',
                color: theme.text,
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
                background: theme.border,
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
                <span>50%</span>
                <span>95%</span>
            </div>
            </div>

            {/* Deposit Percentage - Always show, but disable when not using bridging loan */}
            <div>
            <label style={{
                fontSize: '14px',
                fontWeight: '600',
                color: usingBridgingLoan ? theme.text : '#9ca3af', // Grayed out when disabled
                marginBottom: '8px',
                display: 'block'
            }}>
                Deposit: {depositPercentage}%
            </label>
            <input
                type="range"
                min="5"
                max="50"
                step="1"
                value={depositPercentage}
                onChange={(e) => setDepositPercentage(Number(e.target.value))}
                disabled={!usingBridgingLoan} // Disable when not using bridging loan
                style={{
                width: '100%',
                height: '6px',
                borderRadius: '3px',
                background: usingBridgingLoan ? theme.border : '#f3f4f6', // Grayed out when disabled
                outline: 'none',
                cursor: usingBridgingLoan ? 'pointer' : 'not-allowed',
                opacity: usingBridgingLoan ? 1 : 0.5 // Make it look disabled
                }}
            />
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '12px',
                color: usingBridgingLoan ? theme.textSecondary : '#9ca3af', // Grayed out when disabled
                marginTop: '4px'
            }}>
                <span>5%</span>
                <span>50%</span>
            </div>
            {!usingBridgingLoan && (
                <p style={{
                fontSize: '11px',
                color: '#9ca3af',
                marginTop: '4px',
                fontStyle: 'italic'
                }}>
                Deposit only applies to bridging loan purchases
                </p>
            )}
            </div>

            {/* Bridging Loan Selector */}
            <div>
            <label style={{
                fontSize: '14px',
                fontWeight: '600',
                color: theme.text,
                marginBottom: '8px',
                display: 'block'
            }}>
                Purchasing Method
            </label>
            <div style={{
                display: 'flex',
                gap: '12px',
                marginTop: '8px'
            }}>
                <label style={{
                display: 'flex',
                alignItems: 'center',
                cursor: 'pointer',
                fontSize: '14px',
                color: theme.text
                }}>
                <input
                    type="radio"
                    name="financingMethod"
                    value="standard"
                    checked={!usingBridgingLoan}
                    onChange={() => setUsingBridgingLoan(false)}
                    style={{ marginRight: '6px' }}
                />
                Cash
                </label>
                <label style={{
                display: 'flex',
                alignItems: 'center',
                cursor: 'pointer',
                fontSize: '14px',
                color: theme.text
                }}>
                <input
                    type="radio"
                    name="financingMethod"
                    value="bridging"
                    checked={usingBridgingLoan}
                    onChange={() => setUsingBridgingLoan(true)}
                    style={{ marginRight: '6px' }}
                />
                Bridging Loan
                </label>
            </div>
            </div>



        {/* Mortgage Type */}
        <div>
        <label style={{
            fontSize: '14px',
            fontWeight: '600',
            color: theme.text,
            marginBottom: '8px',
            display: 'block'
        }}>
            Mortgage Type
        </label>
        <div style={{
            display: 'flex',
            gap: '12px',
            marginTop: '8px'
        }}>
            <label style={{
            display: 'flex',
            alignItems: 'center',
            cursor: 'pointer',
            fontSize: '14px',
            color: theme.text
            }}>
            <input
                type="radio"
                name="mortgageType"
                value="repayment"
                checked={mortgageType === 'repayment'}
                onChange={(e) => setMortgageType(e.target.value)}
                style={{ marginRight: '6px' }}
            />
            Repayment
            </label>
            <label style={{
            display: 'flex',
            alignItems: 'center',
            cursor: 'pointer',
            fontSize: '14px',
            color: theme.text
            }}>
            <input
                type="radio"
                name="mortgageType"
                value="interest-only"
                checked={mortgageType === 'interest-only'}
                onChange={(e) => setMortgageType(e.target.value)}
                style={{ marginRight: '6px' }}
            />
            Interest Only
            </label>
        </div>
        </div>
        </div>

        {/* Results Dashboard */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '20px',
          marginBottom: '32px'
        }}>
          {/* Money In/Out */}
          <div style={{
            padding: '20px',
            backgroundColor: calculations.moneyIn < 0 ? '#fef2f2' : '#f0fdf4',
            borderRadius: '8px',
            border: `1px solid ${calculations.monthlyProfit > 0 ? '#059669' : '#f87171'}`,
            textAlign: 'center'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '8px'
            }}>
              <PieChart style={{ 
                width: '20px', 
                height: '20px', 
                marginRight: '8px', 
                color: calculations.monthlyProfit > 0 ? '#059669' : '#dc2626' 
              }} />
              <h3 style={{
                fontSize: '16px',
                fontWeight: '600',
                color: calculations.monthlyProfit > 0 ? '#059669' : '#dc2626'
              }}>
                Monthly Profit
              </h3>
            </div>
            <p style={{
              fontSize: '2rem',
              fontWeight: 'bold',
              color: calculations.monthlyProfit > 0 ? '#059669' : '#dc2626',
              marginBottom: '4px'
            }}>
              £{Math.abs(calculations.monthlyProfit).toLocaleString()}
            </p>
            <p style={{
              fontSize: '12px',
              color: calculations.monthlyProfit > 0 ? '#047857' : '#991b1b'
            }}>
              {calculations.monthlyProfit > 0 ? 'Positive Cash Flow' : 'Negative Cash Flow'}
            </p>
          </div>

          {/* ROI Percentage */}
          <div style={{
            padding: '20px',
            backgroundColor: '#f0f9ff',
            borderRadius: '8px',
            border: '1px solid #0ea5e9',
            textAlign: 'center'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '8px'
            }}>
              <Percent style={{ 
                width: '20px', 
                height: '20px', 
                marginRight: '8px', 
                color: '#0369a1' 
              }} />
              <h3 style={{
                fontSize: '16px',
                fontWeight: '600',
                color: '#0369a1'
              }}>
                Annual ROI
              </h3>
            </div>
            <p style={{
              fontSize: '2rem',
              fontWeight: 'bold',
              color: '#0369a1',
              marginBottom: '4px'
            }}>
              {calculations.roiPercentage.toFixed(1)}%
            </p>
            <p style={{
              fontSize: '12px',
              color: '#0369a1'
            }}>
              Return on Investment
            </p>
          </div>

          {/* Monthly ROI */}
          <div style={{
            padding: '20px',
            backgroundColor: '#fef3c7',
            borderRadius: '8px',
            border: '1px solid #f59e0b',
            textAlign: 'center'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '8px'
            }}>
              <TrendingUp style={{ 
                width: '20px', 
                height: '20px', 
                marginRight: '8px', 
                color: '#d97706' 
              }} />
              <h3 style={{
                fontSize: '16px',
                fontWeight: '600',
                color: '#d97706'
              }}>
                Monthly ROI
              </h3>
            </div>
            <p style={{
              fontSize: '2rem',
              fontWeight: 'bold',
              color: '#d97706',
              marginBottom: '4px'
            }}>
              {calculations.monthlyRoiPercentage.toFixed(2)}%
            </p>
            <p style={{
              fontSize: '12px',
              color: '#92400e'
            }}>
              Monthly Return Rate
            </p>
          </div>
        </div>

        {/* Detailed Breakdown */}
        <div style={{
          backgroundColor: theme.cardBg,
          borderRadius: '8px',
          padding: '24px',
          border: '1px solid #e5e7eb'
        }}>
          <h3 style={{
            fontSize: '18px',
            fontWeight: '600',
            color: '#111827',
            marginBottom: '20px'
          }}>
            Deal Breakdown
          </h3>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '24px'
          }}>
            {/* Investment Summary */}
            <div>
              <h4 style={{
                fontSize: '16px',
                fontWeight: '600',
                color: theme.text,
                marginBottom: '12px'
              }}>
                Investment Summary
              </h4>
              <div style={{ space: '8px' }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  padding: '8px 0',
                  borderBottom: '1px solid #e5e7eb'
                }}>
                  <span style={{ color: theme.textSecondary }}>Purchase Price:</span>
                  <span style={{ fontWeight: '500' }}>£{purchasePrice.toLocaleString()}</span>
                </div>
                {calculations.usingBridgingLoan && (
                <>
                    <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    padding: '8px 0 8px 24px', // Indented
                    borderBottom: '1px solid #e5e7eb'
                    }}>
                    <span style={{ color: theme.textSecondary, fontSize: '14px' }}>Deposit ({depositPercentage}%):</span>
                    <span style={{ fontWeight: '500', fontSize: '14px' }}>£{calculations.depositAmount.toLocaleString()}</span>
                    </div>
                    <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    padding: '8px 0 8px 24px', // Indented
                    borderBottom: '1px solid #e5e7eb'
                    }}>
                    <span style={{ color: theme.textSecondary, fontSize: '14px' }}>Bridge ({calculations.bridgePercentage}%):</span>
                    <span style={{ fontWeight: '500', fontSize: '14px' }}>£{calculations.bridgeAmount.toLocaleString()}</span>
                    </div>
                </>
                )}
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  padding: '8px 0',
                  borderBottom: '1px solid #e5e7eb'
                }}>
                  <span style={{ color: theme.textSecondary }}>Renovation Costs:</span>
                  <span style={{ fontWeight: '500' }}>£{calculations.totalRenovationCosts.toLocaleString()}</span>
                </div>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  padding: '8px 0',
                  borderBottom: '1px solid #e5e7eb'
                }}>
                  <span style={{ color: theme.textSecondary }}>Total Property Cost:</span>
                  <span style={{ fontWeight: '600', color: '#111827' }}>£{calculations.totalPropertyCost.toLocaleString()}</span>
                </div>
                {/*<div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    padding: '8px 0',
                    borderBottom: '1px solid #e5e7eb'
                }}>
                    <span style={{ color: theme.textSecondary }}>Mortgage ({ltvPercentage}%):</span>
                    <span style={{ fontWeight: '500' }}>£{calculations.mortgageAmount.toLocaleString()}</span>
                </div> */}
                <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    padding: '8px 0',
                    borderBottom: '1px solid #e5e7eb'
                }}>
                    <span style={{ color: theme.textSecondary }}>Required Valuation to Extract all Costs:</span>
                    <span style={{ fontWeight: '500', color: '#2563eb' }}>£{calculations.requiredValuation.toLocaleString()}</span>
                </div>
                <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    padding: '8px 0',
                    borderBottom: '1px solid #e5e7eb'
                }}>
                    <span style={{ color: theme.textSecondary }}>Term Mortgage (LTV: {ltvPercentage}% ):</span>
                    <span style={{ fontWeight: '500', color: '#2563eb' }}>£{calculations.termMortgageAmount.toLocaleString()}</span>
                </div>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  padding: '8px 0',
                  borderTop: '2px solid #374151'
                }}>
                  <span style={{ color: '#111827', fontWeight: '600' }}>Cash Required:</span>
                  <span style={{ fontWeight: '700', color: '#dc2626' }}>£{Math.abs(calculations.moneyIn).toLocaleString()}</span>
                </div>
              </div>
            </div>

            {/* Income Summary */}
            <div>
              <h4 style={{
                fontSize: '16px',
                fontWeight: '600',
                color: theme.text,
                marginBottom: '12px'
              }}>
                Income Summary
              </h4>
              <div style={{ space: '8px' }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  padding: '8px 0',
                  borderBottom: '1px solid #e5e7eb'
                }}>
                  <span style={{ color: theme.textSecondary }}>Rent per Room:</span>
                  <span style={{ fontWeight: '500' }}>£{rentPerRoom}/month</span>
                </div>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  padding: '8px 0',
                  borderBottom: '1px solid #e5e7eb'
                }}>
                  <span style={{ color: theme.textSecondary }}>Number of Rooms:</span>
                  <span style={{ fontWeight: '500' }}>{numberOfRooms}</span>
                </div>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  padding: '8px 0',
                  borderBottom: '1px solid #e5e7eb'
                }}>
                  <span style={{ color: theme.textSecondary }}>Monthly Rent Income:</span>
                  <span style={{ fontWeight: '600', color: '#059669' }}>£{calculations.monthlyRentIncome.toLocaleString()}</span>
                </div>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  padding: '8px 0',
                  borderBottom: '1px solid #e5e7eb'
                }}>
                  <span style={{ color: theme.textSecondary }}>Monthly Mortgage:</span>
                  <span style={{ fontWeight: '500', color: '#dc2626' }}>£{calculations.monthlyMortgagePayment.toLocaleString()}</span>
                </div>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  padding: '8px 0',
                  borderTop: '2px solid #374151'
                }}>
                  <span style={{ color: '#111827', fontWeight: '600' }}>Monthly Profit:</span>
                  <span style={{ 
                    fontWeight: '700', 
                    color: calculations.monthlyProfit > 0 ? '#059669' : '#dc2626' 
                  }}>
                    £{Math.abs(calculations.monthlyProfit).toLocaleString()}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Key Metrics */}
          <div style={{
            marginTop: '24px',
            padding: '16px',
            backgroundColor: 'white',
            borderRadius: '6px',
            border: '1px solid #d1d5db'
          }}>
            <h4 style={{
              fontSize: '16px',
              fontWeight: '600',
              color: theme.text,
              marginBottom: '12px'
            }}>
              Key Performance Metrics
            </h4>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '16px'
            }}>
              <div style={{ textAlign: 'center' }}>
                <p style={{ fontSize: '12px', color: theme.textSecondary, marginBottom: '4px' }}>Annual Rent Income</p>
                <p style={{ fontSize: '18px', fontWeight: '600', color: '#059669' }}>
                  £{calculations.annualRentIncome.toLocaleString()}
                </p>
              </div>
              <div style={{ textAlign: 'center' }}>
                <p style={{ fontSize: '12px', color: theme.textSecondary, marginBottom: '4px' }}>Annual Mortgage Payments</p>
                <p style={{ fontSize: '18px', fontWeight: '600', color: '#dc2626' }}>
                  £{calculations.annualMortgagePayments.toLocaleString()}
                </p>
              </div>
              <div style={{ textAlign: 'center' }}>
                <p style={{ fontSize: '12px', color: theme.textSecondary, marginBottom: '4px' }}>Annual Profit</p>
                <p style={{ fontSize: '18px', fontWeight: '600', color: calculations.annualProfit > 0 ? '#059669' : '#dc2626' }}>
                  £{Math.abs(calculations.annualProfit).toLocaleString()}
                </p>
              </div>
              <div style={{ textAlign: 'center' }}>
                <p style={{ fontSize: '12px', color: theme.textSecondary, marginBottom: '4px' }}>Gross Yield</p>
                <p style={{ fontSize: '18px', fontWeight: '600', color: '#2563eb' }}>
                  {((calculations.annualRentIncome / purchasePrice) * 100).toFixed(1)}%
                </p>
              </div>
            </div>
          </div>

        {/* City Comparison */}
         <div style={{
           marginTop: '16px',
           padding: '16px',
           backgroundColor: '#f0fdf4',
           borderRadius: '6px',
           border: '1px solid #059669'
         }}>
           <h4 style={{
             fontSize: '14px',
             fontWeight: '600',
             color: '#059669',
             marginBottom: '8px'
           }}>
             {cityData?.name} Market Comparison
           </h4>
           <div style={{
             display: 'grid',
             gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
             gap: '12px',
             fontSize: '12px'
           }}>
             <div>
               <span style={{ color: '#047857' }}>Your Rent/Room: </span>
               <span style={{ fontWeight: '600', color: '#059669' }}>£{rentPerRoom}</span>
             </div>
             <div>
               <span style={{ color: '#047857' }}>Market Avg: </span>
               <span style={{ fontWeight: '600', color: '#059669' }}>£{averageRentPerRoom}</span>
             </div>
             <div>
               <span style={{ color: '#047857' }}>Difference: </span>
               <span style={{ 
                 fontWeight: '600', 
                 color: rentPerRoom > averageRentPerRoom ? '#059669' : '#dc2626' 
               }}>
                 {rentPerRoom > averageRentPerRoom ? '+' : ''}£{rentPerRoom - averageRentPerRoom}
               </span>
             </div>
             <div>
               <span style={{ color: '#047857' }}>Premium: </span>
               <span style={{ 
                 fontWeight: '600', 
                 color: rentPerRoom > averageRentPerRoom ? '#059669' : '#dc2626' 
               }}>
                 {(((rentPerRoom - averageRentPerRoom) / averageRentPerRoom) * 100).toFixed(1)}%
               </span>
             </div>
           </div>
         </div>
       </div>
     </div>
   </div>
 );
};

export default DealCalculatorPage;