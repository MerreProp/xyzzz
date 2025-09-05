import React, { useState, useEffect } from 'react';
import { Calculator, Home, PoundSterling, TrendingUp, Building, Calendar, Settings, DollarSign, BarChart3, Target, Briefcase } from 'lucide-react';

// Move component definitions OUTSIDE to prevent re-creation on every render
const GalleryCard = ({ title, icon: Icon, children, size = "medium", highlight = false, accent = false, theme }) => {
  const sizeStyles = {
    small: {
      padding: '1rem',
      minHeight: '120px'
    },
    medium: {
      padding: '1.25rem',
      minHeight: '180px'
    },
    large: {
      padding: '1.5rem',
      minHeight: '240px'
    },
    wide: {
      padding: '1.25rem',
      minHeight: '160px'
    },
    tall: {
      padding: '1.25rem',
      minHeight: '300px'
    }
  };

  return (
    <div 
      style={{
        backgroundColor: highlight ? theme.accent : theme.cardBg,
        borderRadius: '16px',
        boxShadow: highlight ? '0 8px 32px rgba(0, 0, 0, 0.15)' : '0 4px 20px rgba(0, 0, 0, 0.08)',
        border: `1px solid ${highlight ? 'transparent' : theme.border}`,
        marginBottom: '1rem',
        transition: 'all 0.3s ease',
        position: 'relative',
        color: highlight ? 'white' : theme.text,
        ...sizeStyles[size]
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'scale(1.02)';
        e.currentTarget.style.zIndex = '10';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'scale(1)';
        e.currentTarget.style.zIndex = '1';
      }}
    >
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem',
        marginBottom: '1rem',
        paddingBottom: '0.75rem',
        borderBottom: `1px solid ${highlight ? 'rgba(255, 255, 255, 0.2)' : theme.border}`
      }}>
        <div style={{
          padding: '0.5rem',
          borderRadius: '10px',
          backgroundColor: highlight ? 'rgba(255, 255, 255, 0.15)' : `rgba(${theme.accent.slice(1).match(/.{2}/g).map(hex => parseInt(hex, 16)).join(', ')}, 0.1)`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <Icon size={18} style={{ color: highlight ? 'white' : theme.accent }} />
        </div>
        <h3 style={{
          fontSize: '1rem',
          fontWeight: '600',
          margin: 0,
          color: highlight ? 'white' : theme.text
        }}>
          {title}
        </h3>
      </div>
      {children}
    </div>
  );
};

const InputField = ({ label, value, onChange, type = "text", prefix, suffix, step, min, disabled = false, compact = false, theme }) => (
  <div style={{ marginBottom: compact ? '0.5rem' : '0.75rem' }}>
    <label style={{
      display: 'block',
      fontSize: '0.75rem',
      fontWeight: '600',
      color: theme.textSecondary,
      marginBottom: '0.5rem',
      textTransform: 'uppercase',
      letterSpacing: '0.5px'
    }}>
      {label}
    </label>
    <div style={{ position: 'relative' }}>
      <input
        type={type}
        value={value || ''}
        onChange={onChange}
        step={step}
        min={min}
        disabled={disabled}
        style={{
          width: '100%',
          padding: `0.75rem ${suffix ? '2rem' : '0.75rem'} 0.75rem ${prefix ? '1.75rem' : '0.75rem'}`,
          border: `1px solid ${theme.border}`,
          borderRadius: '8px',
          fontSize: '0.875rem',
          backgroundColor: theme.cardBg,
          color: theme.text,
          transition: 'all 0.2s ease',
          outline: 'none',
          boxSizing: 'border-box'
        }}
        onFocus={(e) => {
          if (!disabled) {
            e.target.style.borderColor = theme.accent;
            e.target.style.boxShadow = `0 0 0 3px rgba(${theme.accent.slice(1).match(/.{2}/g).map(hex => parseInt(hex, 16)).join(', ')}, 0.1)`;
          }
        }}
        onBlur={(e) => {
          e.target.style.borderColor = theme.border;
          e.target.style.boxShadow = 'none';
        }}
      />
      {prefix && (
        <span style={{
          position: 'absolute',
          left: '0.75rem',
          top: '50%',
          transform: 'translateY(-50%)',
          color: theme.textSecondary,
          fontSize: '0.875rem'
        }}>
          {prefix}
        </span>
      )}
      {suffix && (
        <span style={{
          position: 'absolute',
          right: '0.75rem',
          top: '50%',
          transform: 'translateY(-50%)',
          color: theme.textSecondary,
          fontSize: '0.875rem'
        }}>
          {suffix}
        </span>
      )}
    </div>
  </div>
);

const MetricBadge = ({ label, value, color = '#059669', size = 'medium', theme }) => {
  const sizes = {
    small: { fontSize: '0.875rem', padding: '0.5rem 0.75rem' },
    medium: { fontSize: '1.125rem', padding: '0.75rem 1rem' },
    large: { fontSize: '1.5rem', padding: '1rem 1.25rem' }
  };

  return (
    <div style={{
      backgroundColor: `rgba(${color === '#059669' ? '5, 150, 105' : color === '#dc2626' ? '220, 38, 38' : '37, 99, 235'}, 0.15)`,
      border: `2px solid ${color}`,
      borderRadius: '12px',
      padding: sizes[size].padding,
      textAlign: 'center',
      marginBottom: '0.5rem'
    }}>
      <div style={{ 
        fontSize: '0.65rem', 
        color: theme.textSecondary, 
        marginBottom: '0.25rem',
        fontWeight: '600',
        textTransform: 'uppercase',
        letterSpacing: '0.5px'
      }}>
        {label}
      </div>
      <div style={{ fontSize: sizes[size].fontSize, fontWeight: '700', color: color }}>
        {value}
      </div>
    </div>
  );
};

const BRRRCalculator = ({ theme }) => {
  // We'll assume theme already contains the processed theme data from useTheme and useDarkMode
  // since it's passed as a prop from the parent component
  // State for all inputs
  const [siteDetail, setSiteDetail] = useState({
    address: '',
    dealType: '',
    agentName: '',
    dateEnquired: '',
    dateOffered: '',
    loanType: 'Refurbishment',
    beds: 0,
    sqft: 0,
    gdv: 0,
    annualRent: 0,
    loanTerm: 0,
    rentalDuration: 0
  });

  const [returnMetrics, setReturnMetrics] = useState({
    purchasePrice: 0,
    askingPrice: 0
  });

  const [refurbCosts, setRefurbCosts] = useState({
    refurbishment: { sqft: 0, costPerSqft: 0, total: 0 },
    furniture: { sqft: 0, costPerSqft: 0, total: 0 },
    commercial: { sqft: siteDetail.sqft, costPerSqft: 0, total: 0 },
    fittings: { sqft: 0, costPerSqft: 0, total: 0 },
    demolition: { sqft: 0, costPerSqft: 0, total: 0 },
    siteClearance: { sqft: 0, costPerSqft: 0, total: 0 },
    contingencyRate: 0
  });

  const [financeCosts, setFinanceCosts] = useState({
    bridgingArrangementFeeRate: 0.0,
    developmentArrangementFeeRate: 0,
    surveyCost: 0,
    retainedInterest: 0,
    brokerFee: 0,
    exitFeeRate: 0
  });

  const [transactionCosts, setTransactionCosts] = useState({
    hmoLicense: 0,
    solicitorFee: 0,
  });

  const [monthlyLenderCharges, setMonthlyLenderCharges] = useState({
    bankInterestPCM: 0,
    insurance: 0,
    serviceCharge: 0,
    bills: 0,
    voidMaintenance: 0
  });

  const [debtMetrics, setDebtMetrics] = useState({
    lenderInterestRate: 0,
    grossLTV: 0,
    netLTVDay1: 0,
    grossLTGDV: 0,
    netLTGDV: 0,
    netLTVRefurb: 0
  });

  const [monthlyRunningCostPost, setMonthlyRunningCostPost] = useState({
    managementFeeRate: 0, // NEW: percentage field
    managementFees: 0,    // This will be calculated
    maintenance: 0,
    gasElectric: 0,
    water: 0,
    broadband: 0,
    councilTax: 0,
    insurance: 0,
    tvLicence: 0
  });

  const [refinanceCosts, setRefinanceCosts] = useState({
    refinanceLenderInterest: 0,
    arrangementFeeRate: 0,
    surveyCost: 0,
    solicitorFee: 0,
    exitFeeRate: 0,
    brokerFee: 0 
    });

  const [refinanceMetrics, setRefinanceMetrics] = useState({
    remortgageLTV: 70
  });

  const [incomeMetrics, setIncomeMetrics] = useState({
    rentPCM: 0,
    rentPA: 0
  });

  // Calculated values
  const [calculations, setCalculations] = useState({});

  // Load saved data on component mount
  useEffect(() => {
    const savedData = localStorage.getItem('brrrCalculatorData');
    if (savedData) {
      try {
        const parsedData = JSON.parse(savedData);
        
        // Only restore if data is recent (within 24 hours)
        const savedTime = new Date(parsedData.timestamp);
        const now = new Date();
        const hoursDiff = (now - savedTime) / (1000 * 60 * 60);
        
        if (hoursDiff < 24) {
          setSiteDetail(parsedData.siteDetail || siteDetail);
          setReturnMetrics(parsedData.returnMetrics || returnMetrics);
          setRefurbCosts(parsedData.refurbCosts || refurbCosts);
          setFinanceCosts(parsedData.financeCosts || financeCosts);
          setTransactionCosts(parsedData.transactionCosts || transactionCosts);
          setMonthlyLenderCharges(parsedData.monthlyLenderCharges || monthlyLenderCharges);
          setDebtMetrics(parsedData.debtMetrics || debtMetrics);
          setMonthlyRunningCostPost(parsedData.monthlyRunningCostPost || monthlyRunningCostPost);
          setRefinanceCosts(parsedData.refinanceCosts || refinanceCosts);
          setRefinanceMetrics(parsedData.refinanceMetrics || refinanceMetrics);
          setIncomeMetrics(parsedData.incomeMetrics || incomeMetrics);
        }
      } catch (error) {
        console.error('Error loading saved calculator data:', error);
      }
    }
  }, []); // Empty dependency array - only run on mount

  // Calculate all derived values
  useEffect(() => {
    calculateAll();
  }, [siteDetail, returnMetrics, refurbCosts, financeCosts, transactionCosts, monthlyLenderCharges, debtMetrics, monthlyRunningCostPost, refinanceCosts, refinanceMetrics]);

  useEffect(() => {
    const updatedRefurbCosts = { ...refurbCosts };
    
    Object.keys(updatedRefurbCosts).forEach(key => {
      if (key !== 'contingencyRate' && typeof updatedRefurbCosts[key] === 'object') {
        const newTotal = siteDetail.sqft * updatedRefurbCosts[key].costPerSqft;
        updatedRefurbCosts[key] = {
          ...updatedRefurbCosts[key],
          sqft: siteDetail.sqft,
          total: newTotal
        };
      }
    });
    
    setRefurbCosts(updatedRefurbCosts);
  }, [siteDetail.sqft]); // Remove refurbCosts from dependency array

  // Auto-save all form data to localStorage
  useEffect(() => {
    const formData = {
      siteDetail,
      returnMetrics,
      refurbCosts,
      financeCosts,
      transactionCosts,
      monthlyLenderCharges,
      debtMetrics,
      monthlyRunningCostPost,
      refinanceCosts,
      refinanceMetrics,
      incomeMetrics,
      timestamp: new Date().toISOString()
    };
    
    localStorage.setItem('brrrCalculatorData', JSON.stringify(formData));
  }, [siteDetail, returnMetrics, refurbCosts, financeCosts, transactionCosts, monthlyLenderCharges, debtMetrics, monthlyRunningCostPost, refinanceCosts, refinanceMetrics, incomeMetrics]);

  // Add this right after your auto-save useEffect
  useEffect(() => {
    console.log('Data saved to localStorage:', {
      siteDetailAddress: siteDetail.address,
      purchasePrice: returnMetrics.purchasePrice
    });
  }, [siteDetail, returnMetrics, refurbCosts, financeCosts, transactionCosts, monthlyLenderCharges, debtMetrics, monthlyRunningCostPost, refinanceCosts, refinanceMetrics, incomeMetrics]);

  const clearSavedData = () => {
    localStorage.removeItem('brrrCalculatorData');
    // Reset all state to initial values
    window.location.reload(); // Simple way to reset everything
  };
  

  const calculateAll = () => {
    // Basic calculations
    const monthlyRent = siteDetail.annualRent / 12;
    const grossYield = siteDetail.annualRent / siteDetail.gdv;
    const gdvPerSqft = siteDetail.gdv / siteDetail.sqft;
    const rentPerSqft = siteDetail.annualRent / siteDetail.sqft;

    // Refurbishment calculations
    const subtotalRefurbCost = Object.values(refurbCosts)
      .filter(item => typeof item === 'object' && item.total)
      .reduce((sum, item) => sum + item.total, 0);
    
    const contingencyAmount = subtotalRefurbCost * (refurbCosts.contingencyRate / 100);
    const totalRefurbCost = subtotalRefurbCost + contingencyAmount;

    // Finance Cost calculations
    const bridgingArrangementFee = returnMetrics.purchasePrice * (financeCosts.bridgingArrangementFeeRate / 100);
    const developmentArrangementFee = returnMetrics.purchasePrice * (financeCosts.developmentArrangementFeeRate / 100);
    const exitFee = returnMetrics.purchasePrice * (financeCosts.exitFeeRate / 100);
    const totalFinanceCost = bridgingArrangementFee + developmentArrangementFee + financeCosts.surveyCost + 
                           financeCosts.retainedInterest + financeCosts.brokerFee + exitFee;

    // Transaction and Red Tape Cost
    const totalTransactionCost = transactionCosts.hmoLicense + transactionCosts.solicitorFee;

    // Monthly Lender Charges for Serviced Loans - Day 1
    const totalMonthlyBankCharges = Object.values(monthlyLenderCharges).reduce((sum, cost) => sum + cost, 0);

    // Retained Interest Loan Breakdown
    const grossLoanAmount = returnMetrics.purchasePrice * (debtMetrics.grossLTV / 100);
    const acquisitionFacility = returnMetrics.purchasePrice * (debtMetrics.netLTVDay1 / 100);
    const developmentFacility = totalRefurbCost;
    const financeFacility = financeCosts.retainedInterest + developmentArrangementFee + exitFee;
    const netLoanAmount = acquisitionFacility + developmentFacility;

    // Total Project Cost
    const totalProjectCost = returnMetrics.purchasePrice + totalRefurbCost + totalFinanceCost + totalTransactionCost;
    const netInitialMortgage = netLoanAmount;

    // Total Capital Invested Summary
    const depositAmount = returnMetrics.purchasePrice - acquisitionFacility;
    const sdlt = 0; // From Excel
    const totalCapitalInvested = depositAmount + sdlt + (totalRefurbCost - developmentFacility) + 
                                (totalFinanceCost - financeFacility) + totalTransactionCost;

    // Income Metrics
    const rentPCM = monthlyRent;
    const rentPA = siteDetail.annualRent;

    // Calculate management fees from percentage
    const managementFees = (rentPCM * monthlyRunningCostPost.managementFeeRate) / 100;

    // Monthly Running Cost Post Refurbishment
    const totalMonthlyRunningCostPost = managementFees + 
      monthlyRunningCostPost.maintenance + 
      monthlyRunningCostPost.gasElectric + 
      monthlyRunningCostPost.water + 
      monthlyRunningCostPost.broadband + 
      monthlyRunningCostPost.councilTax + 
      monthlyRunningCostPost.insurance + 
      monthlyRunningCostPost.tvLicence;

    // Monthly Running Cost Inc. Finance
    const monthlyRunningCostIncFinance = totalMonthlyRunningCostPost + totalMonthlyBankCharges;

    // Refinance Costs
    const refinanceArrangementFee = siteDetail.gdv * (refinanceCosts.arrangementFeeRate / 100);
    const refinanceExitFee = grossLoanAmount * (refinanceCosts.exitFeeRate / 100);
    const totalRefinanceCosts = refinanceArrangementFee + refinanceCosts.surveyCost + 
                               refinanceCosts.solicitorFee + refinanceExitFee + refinanceCosts.brokerFee;

    // Refinance Metrics & Costs
    const remortgageAmount = siteDetail.gdv * (refinanceMetrics.remortgageLTV / 100);
    const releasedFunds = remortgageAmount - grossLoanAmount - totalRefinanceCosts;
    const moneyLeftIn = totalCapitalInvested - Math.max(0, releasedFunds);

    // Total Monthly Cost after Refurbishment & Refinance
    const monthlyMortgagePayment = (remortgageAmount * (refinanceCosts.refinanceLenderInterest / 100)) / 12;
    const totalMonthlyCostAfterRefinance = monthlyMortgagePayment + totalMonthlyRunningCostPost;

    // Return Summary After Refinance
    const netIncomePCM = rentPCM - totalMonthlyCostAfterRefinance;
    const netIncomePA = netIncomePCM * 12;
    const leveredROCE = moneyLeftIn > 0 ? (netIncomePA / moneyLeftIn) : 0;

    setCalculations({
      monthlyRent,
      grossYield,
      gdvPerSqft,
      rentPerSqft,
      subtotalRefurbCost,
      contingencyAmount,
      totalRefurbCost,
      bridgingArrangementFee,
      developmentArrangementFee,
      exitFee,
      totalFinanceCost,
      totalTransactionCost,
      totalMonthlyBankCharges,
      grossLoanAmount,
      acquisitionFacility,
      developmentFacility,
      financeFacility,
      netLoanAmount,
      totalProjectCost,
      netInitialMortgage,
      depositAmount,
      sdlt,
      totalCapitalInvested,
      rentPCM,
      rentPA,
      managementFees,
      totalMonthlyRunningCostPost,
      monthlyRunningCostIncFinance,
      refinanceArrangementFee,
      refinanceExitFee,
      totalRefinanceCosts,
      remortgageAmount,
      releasedFunds,
      moneyLeftIn,
      monthlyMortgagePayment,
      totalMonthlyCostAfterRefinance,
      netIncomePCM,
      netIncomePA,
      leveredROCE
    });
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency: 'GBP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value || 0);
  };

  const formatPercentage = (value) => {
    return `${((value || 0) * 100).toFixed(1)}%`;
  };

  return (
    <div style={{ 
      maxWidth: '1400px', 
      margin: '0 auto', 
      padding: '1rem',
      backgroundColor: theme.mainBg,
      minHeight: '100vh',
      transition: 'background-color 0.3s ease'
    }}>
      {/* Gallery Wall Layout */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '1.5rem',
        gridAutoRows: 'minmax(120px, auto)'
      }}>
        
       {/* Site Detail - Large Hero Card */}
        <div style={{ gridColumn: 'span 2' }}>
          <GalleryCard title="Site Detail" icon={Home} size="large" highlight={true} theme={theme}>
            <div style={{
              display: 'grid',
              gridTemplateColumns: '2fr 1fr',
              gap: '1rem',
              marginBottom: '1rem'
            }}>
              <InputField
                label="Site Address"
                value={siteDetail.address}
                onChange={(e) => setSiteDetail({...siteDetail, address: e.target.value})}
                theme={theme}
              />
              <InputField
                label="Deal Type"
                value={siteDetail.dealType}
                onChange={(e) => setSiteDetail({...siteDetail, dealType: e.target.value})}
                theme={theme}
              />
            </div>
            
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr 1fr',
              gap: '1rem',
              marginBottom: '1rem'
            }}>
              <InputField
                label="Agent/Developer"
                value={siteDetail.agentName}
                onChange={(e) => setSiteDetail({...siteDetail, agentName: e.target.value})}
                compact={true}
                theme={theme}
              />
              <InputField
                label="Date Enquired"
                type="date"
                value={siteDetail.dateEnquired}
                onChange={(e) => setSiteDetail({...siteDetail, dateEnquired: e.target.value})}
                compact={true}
                theme={theme}
              />
              <InputField
                label="Date Offered"
                type="date"
                value={siteDetail.dateOffered}
                onChange={(e) => setSiteDetail({...siteDetail, dateOffered: e.target.value})}
                compact={true}
                theme={theme}
              />
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr 1fr 1fr',
              gap: '1rem',
              marginBottom: '1rem'
            }}>
              <InputField
                label="Beds"
                type="number"
                value={siteDetail.beds}
                onChange={(e) => setSiteDetail({...siteDetail, beds: parseInt(e.target.value) || 0})}
                compact={true}
                theme={theme}
              />
              <InputField
                label="sq. ft"
                type="number"
                value={siteDetail.sqft}
                onChange={(e) => setSiteDetail({...siteDetail, sqft: parseInt(e.target.value) || 0})}
                compact={true}
                theme={theme}
              />
              <InputField
                label="GDV"
                type="number"
                value={siteDetail.gdv}
                onChange={(e) => setSiteDetail({...siteDetail, gdv: parseInt(e.target.value) || 0})}
                prefix="£"
                compact={true}
                theme={theme}
              />
              <InputField
                label="Annual Rent"
                type="number"
                value={siteDetail.annualRent}
                onChange={(e) => setSiteDetail({...siteDetail, annualRent: parseInt(e.target.value) || 0})}
                prefix="£"
                compact={true}
                theme={theme}
              />
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '1rem'
            }}>
              <InputField
                label="Purchase Price"
                type="number"
                value={returnMetrics.purchasePrice}
                onChange={(e) => setReturnMetrics({...returnMetrics, purchasePrice: parseInt(e.target.value) || 0})}
                prefix="£"
                compact={true}
                theme={theme}
              />
              <InputField
                label="Asking Price"
                type="number"
                value={returnMetrics.askingPrice}
                onChange={(e) => setReturnMetrics({...returnMetrics, askingPrice: parseInt(e.target.value) || 0})}
                prefix="£"
                compact={true}
                theme={theme}
              />
            </div>
            <div style={{
              marginTop: '1rem',
              paddingTop: '1rem',
              borderTop: `1px solid rgba(255, 255, 255, 0.2)`,
              display: 'flex',
              justifyContent: 'flex-end'
            }}>
              <button
                onClick={clearSavedData}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  color: 'rgba(255, 255, 255, 0.9)',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: '8px',
                  fontSize: '0.75rem',
                  fontWeight: '500',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px'
                }}
                onMouseEnter={(e) => {
                  e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.2)';
                  e.target.style.borderColor = 'rgba(255, 255, 255, 0.4)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                  e.target.style.borderColor = 'rgba(255, 255, 255, 0.2)';
                }}
              >
                Reset Calculator
              </button>
            </div>
          </GalleryCard>
        </div>

        {/* Key Metrics Display - Tall Card */}
        <GalleryCard title="Key Metrics" icon={BarChart3} size="tall" accent={true} theme={theme}>
          <MetricBadge 
            label="Gross Yield" 
            value={formatPercentage(calculations.grossYield)}
            color="#059669"
            size="large"
            theme={theme}
          />
          <MetricBadge 
            label="Total Project Cost" 
            value={formatCurrency(calculations.totalProjectCost)}
            color="#dc2626"
            size="medium"
            theme={theme}
          />
          <MetricBadge 
            label="Capital Required" 
            value={formatCurrency(calculations.totalCapitalInvested)}
            color="#2563eb"
            size="medium"
            theme={theme}
          />
          <MetricBadge 
            label="Money Left In" 
            value={formatCurrency(calculations.moneyLeftIn)}
            color="#7c3aed"
            size="medium"
            theme={theme}
          />
        </GalleryCard>

        {/* Refurbishment Costs - Wide Card */}
        <div style={{ gridColumn: 'span 2' }}>
          <GalleryCard title="Refurbishment Costs" icon={Building} size="wide" theme={theme}>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: '1rem'
            }}>
              {Object.entries(refurbCosts).filter(([key]) => key !== 'contingencyRate').map(([key, value]) => (
                <div key={key} style={{
                  backgroundColor: theme.cardBg,
                  border: `1px solid ${theme.border}`,
                  borderRadius: '8px',
                  padding: '0.75rem'
                }}>
                  <div style={{
                    fontSize: '0.75rem',
                    fontWeight: '600',
                    color: theme.text,
                    marginBottom: '0.5rem',
                    textTransform: 'capitalize'
                  }}>
                    {key.replace(/([A-Z])/g, ' $1')}
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                    <InputField
                      label="Sq Ft"
                      type="number"
                      value={value.sqft}
                      onChange={(e) => {
                        const newSqft = parseInt(e.target.value) || 0;
                        const newTotal = newSqft * value.costPerSqft;
                        setRefurbCosts({
                          ...refurbCosts,
                          [key]: { ...value, sqft: newSqft, total: newTotal }
                        });
                      }}
                      compact={true}
                      theme={theme}
                    />
                    <InputField
                      label="£/sqft"
                      type="number"
                      value={value.costPerSqft}
                      onChange={(e) => {
                        const newCostPerSqft = parseFloat(e.target.value) || 0;
                        const newTotal = value.sqft * newCostPerSqft;
                        setRefurbCosts({
                          ...refurbCosts,
                          [key]: { ...value, costPerSqft: newCostPerSqft, total: newTotal }
                        });
                      }}
                      prefix="£"
                      compact={true}
                      theme={theme}
                    />
                  </div>
                  <div style={{
                    marginTop: '0.5rem',
                    fontSize: '0.875rem',
                    fontWeight: '600',
                    color: theme.accent
                  }}>
                    Total: {formatCurrency(value.total)}
                  </div>
                </div>
              ))}
            </div>
            
            <div style={{
              marginTop: '1rem',
              padding: '0.75rem',
              backgroundColor: `rgba(${theme.accent.slice(1).match(/.{2}/g).map(hex => parseInt(hex, 16)).join(', ')}, 0.1)`,
              border: `1px solid ${theme.accent}`,
              borderRadius: '8px',
              display: 'grid',
              gridTemplateColumns: '1fr 1fr 1fr',
              gap: '1rem',
              alignItems: 'center'
            }}>
              <div>
                <InputField
                  label="Contingency %"
                  type="number"
                  value={refurbCosts.contingencyRate}
                  onChange={(e) => setRefurbCosts({...refurbCosts, contingencyRate: parseFloat(e.target.value) || 0})}
                  suffix="%"
                  step="0.1"
                  compact={true}
                  theme={theme}
                />
                  <div style={{ 
                  fontSize: '0.75rem', 
                  color: theme.textSecondary, 
                  marginTop: '0.25rem',
                  textAlign: 'center'
                }}>
                  {formatCurrency(calculations.contingencyAmount)}
                </div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '0.75rem', color: theme.textSecondary }}>Subtotal Refurb Cost</div>
                <div style={{ fontSize: '1.1rem', fontWeight: '700', color: theme.accent }}>
                  {formatCurrency(calculations.subtotalRefurbCost)}
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.75rem', color: theme.textSecondary }}>Total Refurb Cost</div>
                <div style={{ fontSize: '1.25rem', fontWeight: '700', color: theme.accent }}>
                  {formatCurrency(calculations.totalRefurbCost)}
                </div>
              </div>
            </div>
          </GalleryCard>
        </div>

        {/* Finance Costs - Medium Card */}
        <GalleryCard title="Finance Costs" icon={TrendingUp} size="medium" theme={theme}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '0.75rem',
            marginBottom: '1rem'
          }}>
            <InputField
              label="Bridging Rate"
              type="number"
              value={financeCosts.bridgingArrangementFeeRate}
              onChange={(e) => setFinanceCosts({...financeCosts, bridgingArrangementFeeRate: parseFloat(e.target.value) || 0})}
              suffix="%"
              step="0.1"
              compact={true}
              theme={theme}
            />
            <InputField
              label="Dev Rate"
              type="number"
              value={financeCosts.developmentArrangementFeeRate}
              onChange={(e) => setFinanceCosts({...financeCosts, developmentArrangementFeeRate: parseFloat(e.target.value) || 0})}
              suffix="%"
              step="0.1"
              compact={true}
              theme={theme}
            />
          </div>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '0.75rem'
          }}>
            <InputField
              label="Survey Cost"
              type="number"
              value={financeCosts.surveyCost}
              onChange={(e) => setFinanceCosts({...financeCosts, surveyCost: parseInt(e.target.value) || 0})}
              prefix="£"
              compact={true}
              theme={theme}
            />
            <InputField
              label="Broker Fee"
              type="number"
              value={financeCosts.brokerFee}
              onChange={(e) => setFinanceCosts({...financeCosts, brokerFee: parseInt(e.target.value) || 0})}
              prefix="£"
              compact={true}
              theme={theme}
            />
          </div>
          
          <MetricBadge 
            label="Total Finance Cost" 
            value={formatCurrency(calculations.totalFinanceCost)}
            color="#dc2626"
            size="medium"
            theme={theme}
          />
        </GalleryCard>

        {/* Debt Metrics - Medium Card */}
        <GalleryCard title="Debt Metrics" icon={BarChart3} size="medium" theme={theme}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '0.75rem'
          }}>
            <InputField
              label="Interest Rate"
              type="number"
              value={debtMetrics.lenderInterestRate}
              onChange={(e) => setDebtMetrics({...debtMetrics, lenderInterestRate: parseFloat(e.target.value) || 0})}
              suffix="%"
              step="0.1"
              compact={true}
              theme={theme}
            />
            <InputField
              label="Gross LTV"
              type="number"
              value={debtMetrics.grossLTV}
              onChange={(e) => setDebtMetrics({...debtMetrics, grossLTV: parseFloat(e.target.value) || 0})}
              suffix="%"
              step="0.1"
              compact={true}
              theme={theme}
            />
            <InputField
              label="Net LTV Day 1"
              type="number"
              value={debtMetrics.netLTVDay1}
              onChange={(e) => setDebtMetrics({...debtMetrics, netLTVDay1: parseFloat(e.target.value) || 0})}
              suffix="%"
              step="0.1"
              compact={true}
              theme={theme}
            />
            <InputField
              label="Net LTGDV"
              type="number"
              value={debtMetrics.netLTGDV}
              onChange={(e) => setDebtMetrics({...debtMetrics, netLTGDV: parseFloat(e.target.value) || 0})}
              suffix="%"
              step="0.1"
              compact={true}
              theme={theme}
            />
          </div>
        </GalleryCard>

        {/* Transaction Costs - Small Card */}
        <GalleryCard title="Transaction Costs" icon={Settings} size="small" theme={theme}>
          <InputField
            label="HMO License"
            type="number"
            value={transactionCosts.hmoLicense}
            onChange={(e) => setTransactionCosts({...transactionCosts, hmoLicense: parseInt(e.target.value) || 0})}
            prefix="£"
            compact={true}
            theme={theme}
          />
          <InputField
            label="Solicitor Fee"
            type="number"
            value={transactionCosts.solicitorFee}
            onChange={(e) => setTransactionCosts({...transactionCosts, solicitorFee: parseInt(e.target.value) || 0})}
            prefix="£"
            compact={true}
            theme={theme}
          />
          <MetricBadge 
            label="Total" 
            value={formatCurrency(calculations.totalTransactionCost)}
            color="#059669"
            size="small"
            theme={theme}
          />
        </GalleryCard>

        {/* Monthly Charges - Wide Card */}
        <div style={{ gridColumn: 'span 2' }}>
          <GalleryCard title="Monthly Running Costs" icon={Calendar} size="wide" theme={theme}>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
              gap: '1rem',
              marginBottom: '1rem'
            }}>
              <div style={{
                backgroundColor: theme.cardBg,
                border: `1px solid ${theme.border}`,
                borderRadius: '8px',
                padding: '0.75rem'
              }}>
                <div style={{ fontSize: '0.75rem', fontWeight: '600', color: theme.text, marginBottom: '0.75rem' }}>
                  Lender Charges (Day 1)
                </div>
                <InputField
                  label="Bank Interest"
                  type="number"
                  value={monthlyLenderCharges.bankInterestPCM}
                  onChange={(e) => setMonthlyLenderCharges({...monthlyLenderCharges, bankInterestPCM: parseInt(e.target.value) || 0})}
                  prefix="£"
                  compact={true}
                  theme={theme}
                />
                <InputField
                  label="Insurance"
                  type="number"
                  value={monthlyLenderCharges.insurance}
                  onChange={(e) => setMonthlyLenderCharges({...monthlyLenderCharges, insurance: parseInt(e.target.value) || 0})}
                  prefix="£"
                  compact={true}
                  theme={theme}
                />
                <InputField
                  label="Service Charge"
                  type="number"
                  value={monthlyLenderCharges.bills}
                  onChange={(e) => setMonthlyLenderCharges({...monthlyLenderCharges, bills: parseInt(e.target.value) || 0})}
                  prefix="£"
                  compact={true}
                  theme={theme}
                />
                <InputField
                  label="Bills"
                  type="number"
                  value={monthlyLenderCharges.voidMaintenance}
                  onChange={(e) => setMonthlyLenderCharges({...monthlyLenderCharges, voidMaintenance: parseInt(e.target.value) || 0})}
                  prefix="£"
                  compact={true}
                  theme={theme}
                />
                <InputField
                  label="Void + Maintenance"
                  type="number"
                  value={monthlyLenderCharges.serviceCharge}
                  onChange={(e) => setMonthlyLenderCharges({...monthlyLenderCharges, serviceCharge: parseInt(e.target.value) || 0})}
                  prefix="£"
                  compact={true}
                  theme={theme}
                />
              </div>

              <div style={{
                backgroundColor: theme.cardBg,
                border: `1px solid ${theme.border}`,
                borderRadius: '8px',
                padding: '0.75rem'
              }}>
                <div style={{ fontSize: '0.75rem', fontWeight: '600', color: theme.text, marginBottom: '0.75rem' }}>
                  Post Refurbishment
                </div>
                  <InputField
                  label="Management %"
                  type="number"
                  value={monthlyRunningCostPost.managementFeeRate}
                  onChange={(e) => setMonthlyRunningCostPost({...monthlyRunningCostPost, managementFeeRate: parseFloat(e.target.value) || 0})}
                  suffix="%"
                  step="0.1"
                  compact={true}
                  theme={theme}
                />
                <div style={{ 
                  fontSize: '0.75rem', 
                  color: theme.textSecondary, 
                  marginTop: '0.25rem',
                  textAlign: 'center'
                }}>
                  {formatCurrency(calculations.managementFees)}
                </div>
                <InputField
                  label="Maintenance"
                  type="number"
                  value={monthlyRunningCostPost.maintenance}
                  onChange={(e) => setMonthlyRunningCostPost({...monthlyRunningCostPost, maintenance: parseInt(e.target.value) || 0})}
                  prefix="£"
                  compact={true}
                  theme={theme}
                />
                <InputField
                  label="Gas & Electric"
                  type="number"
                  value={monthlyRunningCostPost.gasElectric}
                  onChange={(e) => setMonthlyRunningCostPost({...monthlyRunningCostPost, gasElectric: parseInt(e.target.value) || 0})}
                  prefix="£"
                  compact={true}
                  theme={theme}
                />
              </div>

              <div style={{
                backgroundColor: theme.cardBg,
                border: `1px solid ${theme.border}`,
                borderRadius: '8px',
                padding: '0.75rem'
              }}>
                <div style={{ fontSize: '0.75rem', fontWeight: '600', color: theme.text, marginBottom: '0.75rem' }}>
                  Utilities & Other
                </div>
                <InputField
                  label="Water"
                  type="number"
                  value={monthlyRunningCostPost.water}
                  onChange={(e) => setMonthlyRunningCostPost({...monthlyRunningCostPost, water: parseInt(e.target.value) || 0})}
                  prefix="£"
                  compact={true}
                  theme={theme}
                />
                <InputField
                  label="Council Tax"
                  type="number"
                  value={monthlyRunningCostPost.councilTax}
                  onChange={(e) => setMonthlyRunningCostPost({...monthlyRunningCostPost, councilTax: parseInt(e.target.value) || 0})}
                  prefix="£"
                  compact={true}
                  theme={theme}
                />
                <InputField
                  label="Broadband"
                  type="number"
                  value={monthlyRunningCostPost.broadband}
                  onChange={(e) => setMonthlyRunningCostPost({...monthlyRunningCostPost, broadband: parseInt(e.target.value) || 0})}
                  prefix="£"
                  compact={true}
                  theme={theme}
                />
                <InputField
                  label="Insurance"
                  type="number"
                  value={monthlyRunningCostPost.insurance}
                  onChange={(e) => setMonthlyRunningCostPost({...monthlyRunningCostPost, insurance: parseInt(e.target.value) || 0})}
                  prefix="£"
                  compact={true}
                  theme={theme}
                />
                <InputField
                  label="TV Licence"
                  type="number"
                  value={monthlyRunningCostPost.tvLicence}
                  onChange={(e) => setMonthlyRunningCostPost({...monthlyRunningCostPost, tvLicence: parseInt(e.target.value) || 0})}
                  prefix="£"
                  compact={true}
                  theme={theme}
                />
              </div>
            </div>
            
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr 1fr',
              gap: '1rem'
            }}>
              <MetricBadge 
                label="Total Monthly Charges" 
                value={formatCurrency(calculations.totalMonthlyBankCharges)}
                color="#dc2626"
                size="small"
                theme={theme}
              />
              <MetricBadge 
                label="Post Refurb Costs" 
                value={formatCurrency(calculations.totalMonthlyRunningCostPost)}
                color="#dc2626"
                size="small"
                theme={theme}
              />
              <MetricBadge 
                label="Running Cost Inc Finance" 
                value={formatCurrency(calculations.monthlyRunningCostIncFinance)}
                color="#dc2626"
                size="small"
                theme={theme}
              />
            </div>
          </GalleryCard>
        </div>

        {/* Capital Invested - Medium Card */}
        <GalleryCard title="Capital Invested" icon={Briefcase} size="medium" accent={true} theme={theme}>
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '0.5rem',
            fontSize: '0.75rem'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Deposit:</span>
              <span style={{ fontWeight: '600' }}>{formatCurrency(calculations.depositAmount)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>SDLT:</span>
              <span style={{ fontWeight: '600' }}>{formatCurrency(calculations.sdlt)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Refurb Cost:</span>
              <span style={{ fontWeight: '600' }}>{formatCurrency(calculations.totalRefurbCost - calculations.developmentFacility)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Finance Cost:</span>
              <span style={{ fontWeight: '600' }}>{formatCurrency(calculations.totalFinanceCost - calculations.financeFacility)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Transaction Cost:</span>
              <span style={{ fontWeight: '600' }}>{formatCurrency(calculations.totalTransactionCost)}</span>
            </div>
          </div>
          
          <MetricBadge 
            label="Total Capital Invested" 
            value={formatCurrency(calculations.totalCapitalInvested)}
            color="#2563eb"
            size="large"
            theme={theme}
          />
        </GalleryCard>

        {/* Loan Breakdown - Medium Card */}
        <GalleryCard title="Loan Breakdown" icon={TrendingUp} size="medium" theme={theme}>
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '0.5rem',
            fontSize: '0.75rem',
            marginBottom: '1rem'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Gross Loan Amount:</span>
              <span style={{ fontWeight: '600' }}>{formatCurrency(calculations.grossLoanAmount)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Acquisition Facility:</span>
              <span style={{ fontWeight: '600' }}>{formatCurrency(calculations.acquisitionFacility)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Development Facility:</span>
              <span style={{ fontWeight: '600' }}>{formatCurrency(calculations.developmentFacility)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Finance Facility:</span>
              <span style={{ fontWeight: '600' }}>{formatCurrency(calculations.financeFacility)}</span>
            </div>
          </div>
          
          <MetricBadge 
            label="Net Loan Amount" 
            value={formatCurrency(calculations.netLoanAmount)}
            color="#059669"
            size="large"
            theme={theme}
          />
        </GalleryCard>

        {/* Income Metrics - Small Card */}
        <GalleryCard title="Income Metrics" icon={DollarSign} size="small" theme={theme}>
          <MetricBadge 
            label="Rent PCM" 
            value={formatCurrency(calculations.rentPCM)}
            color="#059669"
            size="medium"
            theme={theme}
          />
          <MetricBadge 
            label="Rent PA" 
            value={formatCurrency(calculations.rentPA)}
            color="#059669"
            size="small"
            theme={theme}
          />
        </GalleryCard>

        {/* Refinance Costs - Medium Card */}
        <GalleryCard title="Refinance Costs" icon={Calculator} size="medium" theme={theme}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '0.75rem',
            marginBottom: '1rem'
          }}>
            <div style={{
              display: 'grid',
              gridTemplateColumns: '80px 1fr',
              gap: '0.5rem',
              alignItems: 'end'
            }}>
              <InputField
                label="Arrangement Fee"
                type="number"
                value={refinanceCosts.arrangementFeeRate}
                onChange={(e) => setRefinanceCosts({...refinanceCosts, arrangementFeeRate: parseFloat(e.target.value) || 0})}
                suffix="%"
                step="0.1"
                compact={true}
                theme={theme}
              />
              <div style={{ 
                padding: '0.75rem',
                border: `1px solid ${theme.border}`,
                borderRadius: '8px',
                backgroundColor: theme.cardBg,
                textAlign: 'center',
                fontSize: '1rem',
                fontWeight: '600',
                color: theme.accent
              }}>
                {formatCurrency(calculations.refinanceArrangementFee)}
              </div>
            </div>
            <InputField
              label="Exit Fee Rate"
              type="number"
              value={refinanceCosts.exitFeeRate}
              onChange={(e) => setRefinanceCosts({...refinanceCosts, exitFeeRate: parseFloat(e.target.value) || 0})}
              suffix="%"
              step="0.1"
              compact={true}
              theme={theme}
            />
            <InputField
              label="Survey Cost"
              type="number"
              value={refinanceCosts.surveyCost}
              onChange={(e) => setRefinanceCosts({...refinanceCosts, surveyCost: parseInt(e.target.value) || 0})}
              prefix="£"
              compact={true}
              theme={theme}
            />
            <InputField
              label="Solicitor Fee"
              type="number"
              value={refinanceCosts.solicitorFee}
              onChange={(e) => setRefinanceCosts({...refinanceCosts, solicitorFee: parseInt(e.target.value) || 0})}
              prefix="£"
              compact={true}
              theme={theme}
            />
            <InputField
              label="Broker Fee"
              type="number"
              value={refinanceCosts.brokerFee}
              onChange={(e) => setRefinanceCosts({...refinanceCosts, brokerFee: parseInt(e.target.value) || 0})}
              prefix="£"
              compact={true}
              theme={theme}
            />
            <InputField
              label="Refinance Lender Interest Rate"
              type="number"
              value={refinanceCosts.refinanceLenderInterest}
              onChange={(e) => setRefinanceCosts({...refinanceCosts, refinanceLenderInterest: parseFloat(e.target.value) || 0})}
              suffix="%"
              step="0.1"
              compact={true}
              theme={theme}
            />
          </div>
          
          <InputField
            label="Remortgage LTV"
            type="number"
            value={refinanceMetrics.remortgageLTV}
            onChange={(e) => setRefinanceMetrics({...refinanceMetrics, remortgageLTV: parseFloat(e.target.value) || 0})}
            suffix="%"
            step="0.1"
            compact={true}
            theme={theme}
          />
        </GalleryCard>

        {/* Refinance Metrics - Wide Card */}
        <div style={{ gridColumn: 'span 2' }}>
          <GalleryCard title="Refinance Summary" icon={Target} size="wide" accent={true} theme={theme}>
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr 1fr 1fr',
              gap: '1rem'
            }}>
              <MetricBadge 
                label="GDV" 
                value={formatCurrency(siteDetail.gdv)}
                color="#059669"
                size="medium"
                theme={theme}
              />
              <MetricBadge 
                label="Remortgage Amount" 
                value={formatCurrency(calculations.remortgageAmount)}
                color="#2563eb"
                size="medium"
                theme={theme}
              />
              <MetricBadge 
                label="Released Funds" 
                value={formatCurrency(calculations.releasedFunds)}
                color={calculations.releasedFunds > 0 ? "#059669" : "#dc2626"}
                size="medium"
                theme={theme}
              />
              <MetricBadge 
                label="Money Left In" 
                value={formatCurrency(calculations.moneyLeftIn)}
                color="#7c3aed"
                size="large"
                theme={theme}
              />
            </div>
          </GalleryCard>
        </div>

        {/* Monthly Cost After Refinance - Small Highlight Card */}
        <GalleryCard title="Monthly Cost Post-Refinance" icon={Calendar} size="small" highlight={true} theme={theme}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '1.5rem', fontWeight: '700', marginBottom: '0.5rem' }}>
              {formatCurrency(calculations.totalMonthlyCostAfterRefinance)}
            </div>
            <div style={{ fontSize: '0.75rem', opacity: 0.9 }}>
              Total Monthly Cost
            </div>
          </div>
        </GalleryCard>

        {/* Return Summary - Large Highlight Card */}
        <GalleryCard title="Return Summary After Refinance" icon={Target} size="large" highlight={true} theme={theme}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '1rem',
            marginBottom: '1rem'
          }}>
            <div style={{
              backgroundColor: 'rgba(255, 255, 255, 0.2)',
              borderRadius: '12px',
              padding: '1rem',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '0.75rem', opacity: 0.9, marginBottom: '0.5rem' }}>
                Levered ROCE
              </div>
              <div style={{ fontSize: '2rem', fontWeight: '700' }}>
                {formatPercentage(calculations.leveredROCE)}
              </div>
            </div>
            
            <div style={{
              backgroundColor: 'rgba(255, 255, 255, 0.2)',
              borderRadius: '12px',
              padding: '1rem',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '0.75rem', opacity: 0.9, marginBottom: '0.5rem' }}>
                Net Income PCM
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: '700' }}>
                {formatCurrency(calculations.netIncomePCM)}
              </div>
            </div>
          </div>
          
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '0.5rem',
            fontSize: '0.875rem'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ opacity: 0.9 }}>Net Income PA:</span>
              <span style={{ fontWeight: '600' }}>{formatCurrency(calculations.netIncomePA)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ opacity: 0.9 }}>Money Left In:</span>
              <span style={{ fontWeight: '600' }}>{formatCurrency(calculations.moneyLeftIn)}</span>
            </div>
          </div>
        </GalleryCard>

        {/* Total Project Cost Breakdown - Large Highlight Card */}
        <GalleryCard title="Total Project Cost Breakdown" icon={Calculator} size="large" highlight={true} theme={theme}>
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
            fontSize: '0.875rem',
            marginBottom: '1rem'
          }}>
            {/* Total Project Cost Breakdown */}
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Net Initial Mortgage - Credit:</span>
              <span style={{ color: '#059669' }}>({formatCurrency(calculations.netLoanAmount)})</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Finance Facility:</span>
              <span>{formatCurrency(calculations.financeFacility)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Total Capital Required - Equity:</span>
              <span>{formatCurrency(calculations.totalCapitalInvested)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Refinance Cost:</span>
              <span>{formatCurrency(calculations.totalRefinanceCosts)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Legal:</span>
              <span>{formatCurrency(calculations.totalTransactionCost)}</span>
            </div>
            <div style={{ 
              borderTop: '2px solid rgba(255, 255, 255, 0.3)', 
              paddingTop: '0.75rem',
              marginTop: '0.5rem'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '1.1rem', fontWeight: '700', opacity: 0.9 }}>Total Project Costs:</span>
                <span style={{ fontSize: '1.5rem', fontWeight: '700' }}>{formatCurrency(calculations.totalProjectCost)}</span>
              </div>
            </div>
          </div>
        </GalleryCard>

      </div>
    </div>
  );
};

export default BRRRCalculator;