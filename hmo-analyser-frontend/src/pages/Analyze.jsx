import React, { useState, useEffect } from 'react';
import { ChevronDown } from 'lucide-react';
import { Plus, Activity, CheckCircle, Clock, AlertCircle, BarChart3, History, Database, Settings, TrendingUp, FileText, Search, Filter } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { useDarkMode } from '../contexts/DarkModeContext';
import PropertyForm from '../components/PropertyForm';
import ProgressTracker from '../components/ProgressTracker';
import LastPropertySummary from '../components/LastPropertySummary';
import EnhancedDuplicateModal from '../components/EnhancedDuplicateModal';
import { useAuth } from '../components/AuthContext';
import RecentActivityTable from '../components/RecentActivityTable';
import { useQueryClient } from '@tanstack/react-query';

const Analyze = () => {
  // Use your actual theme hooks
  const { currentPalette } = useTheme();
  const { isDarkMode } = useDarkMode();
  
  const queryClient = useQueryClient();

  // State management
  const [activeTab, setActiveTab] = useState('analyze');
  const [currentAnalysis, setCurrentAnalysis] = useState(null);
  const [analysisStatus, setAnalysisStatus] = useState(null);
  const [healthData, setHealthData] = useState(null);
  const [analysisError, setAnalysisError] = useState(null);
  const [lastProperty, setLastProperty] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);


  // Your actual base colors
  const baseColors = {
    darkSlate: '#2C3E4A',
    lightCream: '#F5F1E8',
    softGray: '#A8A5A0',
  };

  // Your actual theme configuration from Layout.jsx
  const theme = isDarkMode ? {
    mainBg: '#1a2b32',
    cardBg: '#2c3e4a',
    text: baseColors.lightCream,
    textSecondary: '#9ca3af',
    border: 'rgba(180, 180, 180, 0.2)',
    accent: currentPalette.primary,
    accentHover: currentPalette.secondary
  } : {
    mainBg: baseColors.lightCream,
    cardBg: '#ffffff',
    text: baseColors.darkSlate,
    textSecondary: baseColors.softGray,
    border: 'rgba(168, 165, 160, 0.3)',
    accent: currentPalette.accent,
    accentHover: currentPalette.primary
  };

  const { apiRequest } = useAuth();

  // Health check on component mount - replace with your actual API
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch('/api/health');
        const data = await response.json();
        setHealthData(data);
      } catch (error) {
        console.error('Health check failed:', error);
        // Fallback data for demo
        setHealthData({
          database_connected: true,
          total_properties: 1247,
          viable_properties: 892,
          active_tasks: 0
        });
      }
    };
    checkHealth();
  }, []);

  // Load last property - integrate with your LastPropertySummary component
  useEffect(() => {
    const loadLastProperty = async () => {
      try {
        // Use the apiRequest method from AuthContext instead of direct fetch
        const data = await apiRequest('/properties/last');
        setLastProperty(data);
      } catch (error) {
        console.error('Failed to load last property:', error);
        // Don't set error state - just log it
      }
    };
    loadLastProperty();
  }, [apiRequest]);

  const tabs = [
    { id: 'analyze', label: 'Property Analysis', icon: Plus },
    { id: 'bulk', label: 'Bulk Analysis', icon: Database },
    { id: 'activity', label: 'Recent Activity', icon: History }, // ✅ This is correct
    { id: 'settings', label: 'Analysis Settings', icon: Settings }
  ];

  // Integration point for your PropertyForm component
  const handleAnalyzeProperty = async (url) => {
    try {
      console.log('Starting analysis for:', url);
      
      setIsAnalyzing(true);
      setAnalysisError(null);
      setCurrentUrl(url);
      
      // Use the correct API endpoint
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      console.log('Analysis response:', result);

      // Handle duplicate detection response
      if (result.duplicate_detected && result.duplicate_data) {
        // Show duplicate confirmation modal for medium confidence matches
        if (result.duplicate_data.potential_matches?.[0]?.confidence_score < 0.7) {
          setDuplicateData({
            ...result.duplicate_data,
            new_url: url
          });
          setShowDuplicateModal(true);
          return result; // Don't start polling yet
        } else {
          // High confidence matches are auto-linked, proceed with analysis
          console.log('High confidence duplicate auto-linked, proceeding with analysis');
        }
      }

      // Start normal analysis flow
      setCurrentAnalysis(result.task_id);
      setAnalysisStatus(result);
      pollAnalysisStatus(result.task_id);

      return result;

    } catch (error) {
      console.error('Failed to analyze property:', error);
      setAnalysisError(error.message);
      setCurrentAnalysis(null);
      setAnalysisStatus(null);
      throw error;
    } finally {
      setIsAnalyzing(false);
    }
  };

  const pollAnalysisStatus = async (taskId) => {
    const maxAttempts = 60;
    let attempts = 0;

    const poll = async () => {
      try {
        attempts++;
        // Use the correct API endpoint
        const response = await fetch(`/api/analysis/${taskId}`);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const status = await response.json();
        setAnalysisStatus(status);

        if (status.status === 'completed') {
          setCurrentAnalysis(null);

          // ✅ ADD THIS: Invalidate cache to refresh LastPropertySummary
          queryClient.invalidateQueries(['properties-last']);
          queryClient.invalidateQueries(['properties']);

          return;
        } else if (status.status === 'failed') {
          setAnalysisError(status.error || 'Analysis failed');
          setCurrentAnalysis(null);
          return;
        } else if (attempts >= maxAttempts) {
          setAnalysisError('Analysis timed out after 5 minutes');
          setCurrentAnalysis(null);
          return;
        }

        setTimeout(poll, 5000);

      } catch (error) {
        console.error('Error polling status:', error);
        setAnalysisError('Failed to check analysis status');
        setCurrentAnalysis(null);
      }
    };

    setTimeout(poll, 2000);
  };

  // Add duplicate modal state  
  const [duplicateData, setDuplicateData] = useState(null);
  const [showDuplicateModal, setShowDuplicateModal] = useState(false);
  const [currentUrl, setCurrentUrl] = useState('');

  // Handle duplicate modal actions
  const handleLinkToExisting = async () => {
    if (!duplicateData?.potential_matches?.[0]?.property_id || !duplicateData?.new_url) {
      setAnalysisError('Missing data for linking properties');
      setShowDuplicateModal(false);
      return;
    }

    try {
      const response = await fetch(`/api/properties/${duplicateData.potential_matches[0].property_id}/link-url`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          new_url: duplicateData.new_url
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to link URL to existing property');
      }

      setIsAnalyzing(true);
      setShowDuplicateModal(false);
      setDuplicateData(null);
      
      // Start analysis of the existing property
      const analysisResponse = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          url: duplicateData.new_url,
          force_separate: false 
        }),
      });

      if (analysisResponse.ok) {
        const result = await analysisResponse.json();
        setCurrentAnalysis(result.task_id);
        setAnalysisStatus(result);
        pollAnalysisStatus(result.task_id);
      }

    } catch (error) {
      console.error('Failed to link to existing property:', error);
      setAnalysisError('Failed to link to existing property');
      setShowDuplicateModal(false);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // These should be separate, sibling functions:

  const handleCreateSeparate = async () => {
    if (!duplicateData?.new_url) {
      setAnalysisError('Missing URL for separate analysis');
      setShowDuplicateModal(false);
      return;
    }

    try {
      setIsAnalyzing(true);
      setShowDuplicateModal(false);
      setDuplicateData(null);
      
      // Force creation as separate property
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          url: duplicateData.new_url,
          force_separate: true 
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create separate property analysis');
      }

      const result = await response.json();
      setCurrentAnalysis(result.task_id);
      setAnalysisStatus(result);
      pollAnalysisStatus(result.task_id);

    } catch (error) {
      console.error('Failed to create separate analysis:', error);
      setAnalysisError('Failed to create separate analysis');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // SEPARATE FUNCTION - not nested inside the above
  const handleAddSeparateRoom = async (propertyId, newUrl) => {
    try {
      setIsAnalyzing(true);
      setShowDuplicateModal(false);
      setDuplicateData(null);
      
      const response = await fetch('/api/duplicate-actions/add-separate-room', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          property_id: propertyId, 
          new_url: newUrl 
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to add separate room');
      }

      const result = await response.json();
      
      // Invalidate cache to refresh property lists
      queryClient.invalidateQueries(['properties']);
      queryClient.invalidateQueries(['properties-last']);
      
    } catch (error) {
      console.error('Failed to add separate room:', error);
      setAnalysisError('Failed to add separate room');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div style={{ 
      minHeight: '100vh', 
      backgroundColor: theme.mainBg,
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      transition: 'background-color 0.3s ease'
    }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem', position: 'relative' }}>
        
        {/* Header Section */}
        <div style={{ marginBottom: '2rem' }}>
          <h1 style={{
            fontSize: '2rem',
            fontWeight: '700',
            color: theme.text,
            marginBottom: '0.5rem',
            letterSpacing: '-0.025em'
          }}>
            Property Analysis
          </h1>
          <p style={{
            fontSize: '1rem',
            color: theme.textSecondary,
            margin: 0
          }}>
            Analyze properties, track performance, and manage your portfolio
          </p>
        </div>

        {/* System Status - Clean Integration */}
        {healthData?.database_connected && (
          <SystemStatusCard healthData={healthData} theme={theme} currentPalette={currentPalette} />
        )}

        {/* Main Content Card */}
        <div style={{
          backgroundColor: theme.cardBg,
          borderRadius: '16px',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
          border: `1px solid ${theme.border}`,
          transition: 'all 0.3s ease'
        }}>
          
          {/* Tab Navigation */}
          <div style={{
            display: 'flex',
            borderBottom: `1px solid ${theme.border}`,
            overflowX: 'auto'
          }}>
            {tabs.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  padding: '1rem 1.5rem',
                  border: 'none',
                  backgroundColor: activeTab === id ? currentPalette.primary : 'transparent',
                  color: activeTab === id ? 'white' : theme.text,
                  fontSize: '0.875rem',
                  fontWeight: '500',
                  cursor: 'pointer',
                  borderBottom: activeTab === id ? `2px solid ${currentPalette.primary}` : '2px solid transparent',
                  transition: 'all 0.2s ease',
                  whiteSpace: 'nowrap',
                  borderRadius: activeTab === id ? '8px 8px 0 0' : '0'
                }}
                onMouseEnter={(e) => {
                  if (activeTab !== id) {
                    e.currentTarget.style.backgroundColor = `rgba(${currentPalette.primary.slice(1).match(/.{2}/g).map(hex => parseInt(hex, 16)).join(', ')}, 0.1)`;
                  }
                }}
                onMouseLeave={(e) => {
                  if (activeTab !== id) {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }
                }}
              >
                <Icon size={18} />
                {label}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div style={{ padding: '2rem' }}>
            
            {/* Property Analysis Tab */}
              {activeTab === 'analyze' && (
                <div>
                  {/* Compact Analysis Form Section */}
                  <div style={{ marginBottom: '2rem' }}>
                    <h3 style={{
                      fontSize: '1.125rem',
                      fontWeight: '600',
                      color: theme.text,
                      marginBottom: '1rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem'
                    }}>
                      <Plus size={18} style={{ color: currentPalette.primary }} />
                      Quick Analysis
                    </h3>
                    
                    <div style={{
                      backgroundColor: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : '#f8fafc',
                      border: `1px solid ${theme.border}`,
                      borderRadius: '8px',
                      padding: '1rem'
                    }}>
                      <PropertyAnalysisForm 
                        onSubmit={handleAnalyzeProperty}
                        isLoading={isAnalyzing}
                        theme={theme}
                        currentPalette={currentPalette}
                      />
                    </div>
                  </div>

                  {/* Progress indicator - only when analyzing */}
                  {currentAnalysis && (
                    <div style={{ marginBottom: '1.5rem' }}>
                      <div style={{
                        backgroundColor: isDarkMode ? 'rgba(59, 130, 246, 0.1)' : '#eff6ff',
                        border: `1px solid ${isDarkMode ? 'rgba(59, 130, 246, 0.3)' : '#bfdbfe'}`,
                        borderRadius: '8px',
                        padding: '1rem'
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                          <Activity size={16} style={{ color: currentPalette.primary, animation: 'spin 1s linear infinite' }} />
                          <span style={{ fontSize: '0.875rem', fontWeight: '500', color: theme.text }}>
                            Analysis in Progress
                          </span>
                        </div>
                        <div style={{ fontSize: '0.75rem', color: theme.textSecondary }}>
                          Task ID: {currentAnalysis}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Error display - only when errors occur */}
                  {analysisError && (
                    <div style={{
                      backgroundColor: isDarkMode ? 'rgba(239, 68, 68, 0.1)' : '#fef2f2',
                      border: `1px solid ${isDarkMode ? 'rgba(239, 68, 68, 0.3)' : '#fecaca'}`,
                      borderRadius: '8px',
                      padding: '1rem',
                      marginBottom: '1.5rem'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <AlertCircle style={{ width: '16px', height: '16px', color: '#dc2626' }} />
                        <div>
                          <div style={{ fontWeight: '500', color: isDarkMode ? '#fca5a5' : '#991b1b', fontSize: '0.875rem' }}>
                            Analysis Failed
                          </div>
                          <div style={{ fontSize: '0.75rem', color: isDarkMode ? '#fecaca' : '#b91c1c' }}>
                            {analysisError}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Ready state - when not analyzing or errored */}
                  {!currentAnalysis && !analysisError && (
                    <div style={{
                      backgroundColor: isDarkMode ? 'rgba(255, 255, 255, 0.02)' : '#f9fafb',
                      border: `1px solid ${theme.border}`,
                      borderRadius: '8px',
                      padding: '1rem',
                      textAlign: 'center'
                    }}>
                      <div style={{ fontSize: '0.875rem', color: theme.textSecondary, marginBottom: '0.5rem' }}>
                        ✨ Ready to analyze
                      </div>
                      <div style={{ fontSize: '0.75rem', color: theme.textSecondary }}>
                        Enter a SpareRoom URL above to get started
                      </div>
                    </div>
                  )}

                  {/* Enhanced Duplicate Detection Modal */}
                  {showDuplicateModal && duplicateData && (
                    <EnhancedDuplicateModal
                      isOpen={showDuplicateModal}
                      onClose={() => {
                        setShowDuplicateModal(false);
                        setDuplicateData(null);
                      }}
                      duplicateData={duplicateData}
                      onLinkToExisting={handleLinkToExisting}
                      onCreateSeparate={handleCreateSeparate}
                      onAddSeparateRoom={handleAddSeparateRoom}  // ← ADD THIS LINE
                      isLoading={isAnalyzing}
                    />
                  )}
                </div>
              )}

              {/* Recent Activity Tab */}
              {activeTab === 'activity' && (
                <RecentActivityTable 
                  theme={theme} 
                  currentPalette={currentPalette} 
                  isDarkMode={isDarkMode} 
                />
              )}

              {/* Other Tabs - Placeholder for remaining tabs */}
              {activeTab !== 'analyze' && activeTab !== 'activity' && (
                <div style={{ textAlign: 'center', padding: '2rem' }}>
                  <div style={{
                    fontSize: '2rem',
                    marginBottom: '1rem',
                    opacity: 0.3
                  }}>
                    <Settings style={{ width: '32px', height: '32px', color: theme.textSecondary }} />
                  </div>
                  <h3 style={{
                    fontSize: '1rem',
                    fontWeight: '600',
                    color: theme.text,
                    marginBottom: '0.5rem'
                  }}>
                    Coming Soon
                  </h3>
                  <p style={{
                    fontSize: '0.75rem',
                    color: theme.textSecondary,
                    margin: 0
                  }}>
                    This section is under development
                  </p>
                </div>
              )}
            </div>
          </div>
        

          {/* Last Property Summary & Today's Properties - Outside the tabs */}
          <div style={{ marginTop: '2rem' }}>
            <LastPropertySummary />
          </div>
          
          <div style={{ marginTop: '2rem' }}>
            <TodayPropertiesSection theme={theme} currentPalette={currentPalette} />
          </div>
          
        </div>
      
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

// System Status Card Component
const SystemStatusCard = ({ healthData, theme, currentPalette }) => {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: '2rem',
      padding: '0.75rem 0',
      borderBottom: `1px solid ${theme.border}`
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{
            width: '8px',
            height: '8px',
            backgroundColor: '#10b981',
            borderRadius: '50%'
          }} />
          <span style={{ fontSize: '0.875rem', color: theme.textSecondary }}>
            System Online
          </span>
        </div>
        
        <div style={{
          fontSize: '0.875rem',
          color: theme.textSecondary,
          display: 'flex',
          alignItems: 'center',
          gap: '1rem'
        }}>
          <span>{healthData.total_properties} Properties</span>
          <span>{healthData.viable_properties} Viable</span>
        </div>
      </div>

      {healthData.active_tasks > 0 && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          backgroundColor: `rgba(${currentPalette.primary.slice(1).match(/.{2}/g).map(hex => parseInt(hex, 16)).join(', ')}, 0.1)`,
          color: currentPalette.primary,
          padding: '0.25rem 0.75rem',
          borderRadius: '12px',
          fontSize: '0.75rem',
          fontWeight: '500'
        }}>
          <Activity size={12} style={{ animation: 'spin 1s linear infinite' }} />
          {healthData.active_tasks} running
        </div>
      )}
    </div>
  );
};

// Property Analysis Form Component - Replace with your PropertyForm
// Replace the PropertyAnalysisForm component in your Analyze.jsx file with this enhanced version:

// Replace your entire PropertyAnalysisForm component with this complete version:

const PropertyAnalysisForm = ({ onSubmit, isLoading, theme, currentPalette }) => {
  const [url, setUrl] = useState('');
  const [validationError, setValidationError] = useState('');
  const [notification, setNotification] = useState(null);
  const [hasSubmitted, setHasSubmitted] = useState(false);

  // Clear notification after timeout
  useEffect(() => {
    if (notification && notification.type !== 'submitting') {
      const timeout = setTimeout(() => {
        setNotification(null);
      }, 12000); // 12 seconds to give user time to read

      return () => clearTimeout(timeout);
    }
  }, [notification]);

  // Reset form after submission
  useEffect(() => {
    if (!isLoading && hasSubmitted) {
      const timeout = setTimeout(() => {
        setUrl('');
        setHasSubmitted(false);
      }, 4000);

      return () => clearTimeout(timeout);
    }
  }, [isLoading, hasSubmitted]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setValidationError('');
    
    if (!url.trim()) {
      setValidationError('Please enter a property URL');
      return;
    }
    
    if (!url.includes('spareroom.co.uk')) {
      setValidationError('Please enter a valid SpareRoom URL');
      return;
    }
    
    setHasSubmitted(true);
    
    // Show submitting notification
    setNotification({
      type: 'submitting',
      message: 'Starting analysis...'
    });

    try {
      const result = await onSubmit(url.trim());
      
      // Handle the API response and show appropriate notification
      if (result?.property_metadata) {
        setNotification({
          type: result.property_metadata.is_existing ? 'existing' : 'new',
          data: result.property_metadata,
          message: result.message
        });
      } else if (result?.message) {
        setNotification({
          type: 'info',
          message: result.message
        });
      } else {
        setNotification({
          type: 'info',
          message: 'Analysis started successfully!'
        });
      }
    } catch (error) {
      console.error('Analysis error:', error);
      setNotification({
        type: 'error',
        message: 'Failed to start analysis. Please try again.'
      });
      setHasSubmitted(false);
      setUrl('');
    }
  };

  const renderNotification = () => {
    if (!notification) return null;

    const getNotificationConfig = () => {
      switch (notification.type) {
        case 'existing':
          return {
            borderColor: '#f59e0b',
            icon: '🔄',
            title: 'Property Already Analyzed',
            iconBg: 'rgba(245, 158, 11, 0.1)'
          };
        case 'new':
          return {
            borderColor: '#10b981',
            icon: '✨',
            title: 'New Property Detected',
            iconBg: 'rgba(16, 185, 129, 0.1)'
          };
        case 'submitting':
          return {
            borderColor: currentPalette.primary,
            icon: '⏳',
            title: 'Analysis Starting',
            iconBg: `rgba(${currentPalette.primary.slice(1).match(/.{2}/g).map(hex => parseInt(hex, 16)).join(', ')}, 0.1)`
          };
        case 'error':
          return {
            borderColor: '#ef4444',
            icon: '❌',
            title: 'Analysis Failed',
            iconBg: 'rgba(239, 68, 68, 0.1)'
          };
        default:
          return {
            borderColor: currentPalette.primary,
            icon: 'ℹ️',
            title: 'Analysis Update',
            iconBg: `rgba(${currentPalette.primary.slice(1).match(/.{2}/g).map(hex => parseInt(hex, 16)).join(', ')}, 0.1)`
          };
      }
    };

    const config = getNotificationConfig();

    return (
      <div 
        style={{
          marginTop: '1rem',
          backgroundColor: theme.cardBg,
          borderRadius: '12px',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
          border: `1px solid ${theme.border}`,
          borderLeft: `4px solid ${config.borderColor}`,
          transition: 'all 0.3s ease',
          animation: 'slideIn 0.3s ease-out'
        }}
      >
        <style>
          {`
            @keyframes slideIn {
              from { 
                opacity: 0; 
                transform: translateY(-8px); 
              }
              to { 
                opacity: 1; 
                transform: translateY(0); 
              }
            }
          `}
        </style>

        {/* Header Section */}
        <div style={{
          padding: '1rem 1.5rem',
          borderBottom: `1px solid ${theme.border}`,
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem'
        }}>
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '8px',
            backgroundColor: config.iconBg,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1rem',
            flexShrink: 0
          }}>
            {config.icon}
          </div>
          
          <div style={{ flex: 1 }}>
            <h4 style={{
              fontSize: '1rem',
              fontWeight: '600',
              color: theme.text,
              margin: 0,
              marginBottom: '0.25rem'
            }}>
              {config.title}
            </h4>
            <p style={{
              fontSize: '0.875rem',
              color: theme.textSecondary,
              margin: 0,
              lineHeight: '1.4'
            }}>
              {notification.message}
            </p>
          </div>

          {notification.type !== 'submitting' && (
            <button
              onClick={() => setNotification(null)}
              style={{
                background: 'none',
                border: 'none',
                fontSize: '1.25rem',
                cursor: 'pointer',
                color: theme.textSecondary,
                opacity: 0.6,
                flexShrink: 0,
                padding: '0.25rem',
                borderRadius: '4px',
                transition: 'all 0.2s ease'
              }}
              onMouseOver={(e) => {
                e.target.style.opacity = '1';
                e.target.style.backgroundColor = `rgba(${theme.text === '#F5F1E8' ? '255, 255, 255' : '0, 0, 0'}, 0.1)`;
              }}
              onMouseOut={(e) => {
                e.target.style.opacity = '0.6';
                e.target.style.backgroundColor = 'transparent';
              }}
            >
              ×
            </button>
          )}
        </div>

        {/* Metadata Section for Existing Properties */}
        {notification.data && notification.type === 'existing' && (
          <div style={{ padding: '1rem 1.5rem' }}>
            <div style={{
              backgroundColor: theme.text === '#F5F1E8' ? 'rgba(255, 255, 255, 0.05)' : '#f8fafc',
              border: `1px solid ${theme.border}`,
              borderRadius: '8px',
              padding: '1rem'
            }}>
              <div style={{
                fontSize: '0.75rem',
                fontWeight: '500',
                color: theme.textSecondary,
                marginBottom: '0.75rem',
                textTransform: 'uppercase',
                letterSpacing: '0.05em'
              }}>
                Analysis History
              </div>
              
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                gap: '1rem'
              }}>
                <div>
                  <div style={{
                    fontSize: '1.25rem',
                    fontWeight: '600',
                    color: theme.text,
                    marginBottom: '0.25rem'
                  }}>
                    {notification.data.total_analyses}
                  </div>
                  <div style={{
                    fontSize: '0.75rem',
                    color: theme.textSecondary
                  }}>
                    Total Analyses
                  </div>
                </div>
                
                <div>
                  <div style={{
                    fontSize: '1.25rem',
                    fontWeight: '600',
                    color: theme.text,
                    marginBottom: '0.25rem'
                  }}>
                    {notification.data.total_changes || 0}
                  </div>
                  <div style={{
                    fontSize: '0.75rem',
                    color: theme.textSecondary
                  }}>
                    Changes Tracked
                  </div>
                </div>
                
                {notification.data.last_analyzed && (
                  <div style={{ gridColumn: 'span 2' }}>
                    <div style={{
                      fontSize: '0.875rem',
                      fontWeight: '500',
                      color: theme.text,
                      marginBottom: '0.25rem'
                    }}>
                      {new Date(notification.data.last_analyzed).toLocaleDateString('en-US', {
                        weekday: 'short',
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric'
                      })}
                    </div>
                    <div style={{
                      fontSize: '0.75rem',
                      color: theme.textSecondary
                    }}>
                      Last Analyzed
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Action Hint */}
            <div style={{
              marginTop: '0.75rem',
              padding: '0.5rem',
              backgroundColor: `rgba(${currentPalette.primary.slice(1).match(/.{2}/g).map(hex => parseInt(hex, 16)).join(', ')}, 0.05)`,
              borderRadius: '6px',
              fontSize: '0.75rem',
              color: theme.textSecondary,
              textAlign: 'center'
            }}>
              💡 Check "Last Property Analyzed" below for updated results
            </div>
          </div>
        )}

        {/* Loading Progress for Submitting */}
        {notification.type === 'submitting' && (
          <div style={{ padding: '1rem 1.5rem' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              padding: '0.75rem',
              backgroundColor: theme.text === '#F5F1E8' ? 'rgba(255, 255, 255, 0.05)' : '#f8fafc',
              borderRadius: '8px'
            }}>
              <div style={{
                width: '16px',
                height: '16px',
                border: `2px solid ${theme.border}`,
                borderTop: `2px solid ${currentPalette.primary}`,
                borderRadius: '50%',
                animation: 'spin 1s linear infinite'
              }} />
              <span style={{
                fontSize: '0.875rem',
                color: theme.textSecondary
              }}>
                This usually takes 30-60 seconds...
              </span>
            </div>
          </div>
        )}
      </div>
    );
  };

  // 🔧 THIS IS THE MISSING PART - THE ACTUAL FORM RETURN
  return (
    <div>
      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>

      <div style={{ marginBottom: '1rem' }}>
        <label style={{
          display: 'block',
          fontSize: '0.875rem',
          fontWeight: '500',
          color: theme.text,
          marginBottom: '0.5rem'
        }}>
          Property URL
        </label>
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://www.spareroom.co.uk/flatshare/..."
          disabled={isLoading || hasSubmitted}
          style={{
            width: '100%',
            padding: '0.75rem',
            border: `2px solid ${validationError ? '#ef4444' : theme.border}`,
            borderRadius: '8px',
            fontSize: '1rem',
            backgroundColor: (isLoading || hasSubmitted) ? (theme.text === '#F5F1E8' ? '#374151' : '#f3f4f6') : theme.cardBg,
            color: theme.text,
            transition: 'border-color 0.2s ease',
            boxSizing: 'border-box'
          }}
          onFocus={(e) => {
            if (!validationError) {
              e.target.style.borderColor = currentPalette.primary;
              e.target.style.boxShadow = `0 0 0 3px rgba(${currentPalette.primary.slice(1).match(/.{2}/g).map(hex => parseInt(hex, 16)).join(', ')}, 0.1)`;
            }
          }}
          onBlur={(e) => {
            e.target.style.borderColor = validationError ? '#ef4444' : theme.border;
            e.target.style.boxShadow = 'none';
          }}
        />
        {validationError && (
          <div style={{
            fontSize: '0.875rem',
            color: '#ef4444',
            marginTop: '0.5rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <AlertCircle size={16} />
            {validationError}
          </div>
        )}
      </div>
      
      <button
        onClick={handleSubmit}
        disabled={isLoading || hasSubmitted}
        style={{
          backgroundColor: (isLoading || hasSubmitted) ? theme.textSecondary : currentPalette.primary,
          color: 'white',
          padding: '0.75rem 1.5rem',
          border: 'none',
          borderRadius: '8px',
          fontSize: '0.875rem',
          fontWeight: '500',
          cursor: (isLoading || hasSubmitted) ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          transition: 'all 0.2s ease'
        }}
        onMouseEnter={(e) => {
          if (!isLoading && !hasSubmitted) {
            e.target.style.backgroundColor = currentPalette.secondary;
            e.target.style.transform = 'translateY(-1px)';
          }
        }}
        onMouseLeave={(e) => {
          if (!isLoading && !hasSubmitted) {
            e.target.style.backgroundColor = currentPalette.primary;
            e.target.style.transform = 'translateY(0)';
          }
        }}
      >
        {isLoading || hasSubmitted ? (
          <>
            <Activity size={16} style={{ animation: 'spin 1s linear infinite' }} />
            {hasSubmitted ? 'Analysis Started...' : 'Analyzing...'}
          </>
        ) : (
          <>
            <Plus size={16} />
            Analyze Property
          </>
        )}
      </button>

      {renderNotification()}
    </div>
  );
};

// Last Property Card Component - Replace with your LastPropertySummary
const LastPropertyCard = ({ property, theme, currentPalette }) => {
  const formatCurrency = (amount) => {
    return amount ? `£${amount.toLocaleString()}` : 'N/A';
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'active':
        return { bg: 'rgba(34, 197, 94, 0.1)', color: '#166534' };
      case 'sold':
        return { bg: 'rgba(239, 68, 68, 0.1)', color: '#991b1b' };
      case 'under_offer':
        return { bg: 'rgba(245, 158, 11, 0.1)', color: '#92400e' };
      default:
        return { bg: 'rgba(107, 114, 128, 0.1)', color: '#374151' };
    }
  };

  const statusColors = getStatusColor(property.listing_status);

  return (
    <div>
      <h3 style={{
        fontSize: '1.25rem',
        fontWeight: '600',
        color: theme.text,
        marginBottom: '1rem',
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem'
      }}>
        <BarChart3 size={20} style={{ color: currentPalette.primary }} />
        Last Property Analyzed
      </h3>
      
      <div style={{
        backgroundColor: theme.text === '#F5F1E8' ? 'rgba(255, 255, 255, 0.05)' : '#f8fafc',
        border: `1px solid ${theme.border}`,
        borderRadius: '12px',
        padding: '1.5rem'
      }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1.5rem',
          marginBottom: '1.5rem'
        }}>
          <div>
            <div style={{ fontSize: '0.875rem', color: theme.textSecondary, marginBottom: '0.5rem' }}>
              Property Address
            </div>
            <div style={{ fontWeight: '500', color: theme.text }}>
              {property.address}
            </div>
          </div>
          
          <div>
            <div style={{ fontSize: '0.875rem', color: theme.textSecondary, marginBottom: '0.5rem' }}>
              Annual Income
            </div>
            <div style={{ fontWeight: '600', color: currentPalette.primary, fontSize: '1.125rem' }}>
              {formatCurrency(property.annual_income)}
            </div>
          </div>
          
          <div>
            <div style={{ fontSize: '0.875rem', color: theme.textSecondary, marginBottom: '0.5rem' }}>
              Available Rooms
            </div>
            <div style={{ fontWeight: '500', color: theme.text }}>
              {property.available_rooms} rooms
            </div>
          </div>
          
          <div>
            <div style={{ fontSize: '0.875rem', color: theme.textSecondary, marginBottom: '0.5rem' }}>
              Status
            </div>
            <div style={{
              display: 'inline-block',
              backgroundColor: statusColors.bg,
              color: statusColors.color,
              padding: '0.25rem 0.75rem',
              borderRadius: '12px',
              fontSize: '0.75rem',
              fontWeight: '500',
              textTransform: 'capitalize'
            }}>
              {property.listing_status}
            </div>
          </div>
        </div>
        
        <div style={{
          display: 'flex',
          gap: '1rem',
          paddingTop: '1rem',
          borderTop: `1px solid ${theme.border}`
        }}>
          <button 
            style={{
              backgroundColor: currentPalette.primary,
              color: 'white',
              padding: '0.5rem 1rem',
              border: 'none',
              borderRadius: '6px',
              fontSize: '0.875rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.target.style.backgroundColor = currentPalette.secondary;
            }}
            onMouseLeave={(e) => {
              e.target.style.backgroundColor = currentPalette.primary;
            }}
          >
            <FileText size={16} />
            View Details
          </button>
          
          <button style={{
            backgroundColor: 'transparent',
            color: theme.textSecondary,
            padding: '0.5rem 1rem',
            border: `1px solid ${theme.border}`,
            borderRadius: '6px',
            fontSize: '0.875rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            transition: 'all 0.2s ease'
          }}
          onMouseEnter={(e) => {
            e.target.style.backgroundColor = `rgba(${currentPalette.primary.slice(1).match(/.{2}/g).map(hex => parseInt(hex, 16)).join(', ')}, 0.1)`;
            e.target.style.borderColor = currentPalette.primary;
          }}
          onMouseLeave={(e) => {
            e.target.style.backgroundColor = 'transparent';
            e.target.style.borderColor = theme.border;
          }}
          >
            <TrendingUp size={16} />
            View History
          </button>
        </div>
      </div>
    </div>
  );
};

// Today's Properties Section Component
const TodayPropertiesSection = ({ theme, currentPalette }) => {
  const [todayProperties, setTodayProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isExpanded, setIsExpanded] = useState(false);

  // Fetch today's properties - replace with your actual API
  useEffect(() => {
    const fetchTodayProperties = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/properties/today');
        
        if (response.ok) {
          const data = await response.json();
          setTodayProperties(data.properties || []);
        }
      } catch (error) {
        console.error('Error fetching today\'s properties:', error);
        setTodayProperties([]);
      } finally {
        setLoading(false);
      }
    };
    
    fetchTodayProperties();
  }, []);

  if (loading) {
    return (
      <div style={{ marginTop: '2rem' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          marginBottom: '1rem'
        }}>
          <Activity size={16} style={{ color: currentPalette.primary, animation: 'spin 1s linear infinite' }} />
          <span style={{ fontSize: '0.875rem', color: theme.textSecondary }}>
            Loading today's properties...
          </span>
        </div>
      </div>
    );
  }

  const formatCurrency = (amount) => {
    return amount ? `£${amount.toLocaleString()}` : 'N/A';
  };

  const ChevronDown = ({ size, style }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={style}>
      <polyline points="6,9 12,15 18,9"></polyline>
    </svg>
  );

  return (
    <div style={{
      backgroundColor: theme.cardBg,
      borderRadius: '16px',
      boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
      border: `1px solid ${theme.border}`,
      padding: '2rem',
      transition: 'all 0.3s ease'
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '1rem'
      }}>
        <h3 style={{
          fontSize: '1.25rem',
          fontWeight: '600',
          color: theme.text,
          margin: 0,
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem'
        }}>
          <Clock size={20} style={{ color: currentPalette.primary }} />
          Today's Analysis ({todayProperties.length})
        </h3>
        
        {todayProperties.length > 0 && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            style={{
              backgroundColor: 'transparent',
              border: 'none',
              color: currentPalette.primary,
              fontSize: '0.875rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.5rem'
            }}
          >
            {isExpanded ? 'Show Less' : 'Show All'}
            <ChevronDown size={16} style={{
              transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
              transition: 'transform 0.2s ease'
            }} />
          </button>
        )}
      </div>

      {todayProperties.length === 0 ? (
        <div style={{
          backgroundColor: theme.text === '#F5F1E8' ? 'rgba(255, 255, 255, 0.05)' : '#f8fafc',
          border: `1px solid ${theme.border}`,
          borderRadius: '8px',
          padding: '1.5rem',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '0.875rem', color: theme.textSecondary, marginBottom: '0.5rem' }}>
            No properties analyzed today
          </div>
          <div style={{ fontSize: '0.75rem', color: theme.textSecondary }}>
            Properties you analyze will appear here
          </div>
        </div>
      ) : (
        <div>
          {/* Compact Card View */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '1rem',
            marginBottom: isExpanded ? '1rem' : '0'
          }}>
            {todayProperties.slice(0, isExpanded ? todayProperties.length : 2).map((property, index) => (
              <div
                key={property.property_id}
                style={{
                  backgroundColor: theme.text === '#F5F1E8' ? 'rgba(255, 255, 255, 0.05)' : '#ffffff',
                  border: `1px solid ${theme.border}`,
                  borderLeft: `3px solid ${currentPalette.primary}`,
                  borderRadius: '8px',
                  padding: '1rem',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.1)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
                onClick={() => {
                  // Navigate to property details
                  window.location.href = `/property/${property.property_id}`;
                }}
              >
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  marginBottom: '0.75rem'
                }}>
                  <div style={{ flex: 1 }}>
                    <div style={{
                      fontSize: '0.875rem',
                      fontWeight: '500',
                      color: theme.text,
                      marginBottom: '0.25rem'
                    }}>
                      {property.address}
                    </div>
                    <div style={{
                      fontSize: '0.75rem',
                      color: theme.textSecondary
                    }}>
                      Analyzed today
                    </div>
                  </div>
                  
                  <div style={{
                    backgroundColor: `rgba(${currentPalette.primary.slice(1).match(/.{2}/g).map(hex => parseInt(hex, 16)).join(', ')}, 0.1)`,
                    color: currentPalette.primary,
                    padding: '0.25rem 0.5rem',
                    borderRadius: '12px',
                    fontSize: '0.75rem',
                    fontWeight: '500'
                  }}>
                    New
                  </div>
                </div>
                
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div>
                    <div style={{
                      fontSize: '1rem',
                      fontWeight: '600',
                      color: currentPalette.primary
                    }}>
                      {formatCurrency(property.annual_income)}
                    </div>
                    <div style={{
                      fontSize: '0.75rem',
                      color: theme.textSecondary
                    }}>
                      annual income
                    </div>
                  </div>
                  
                  <div style={{
                    textAlign: 'right'
                  }}>
                    <div style={{
                      fontSize: '1rem',
                      fontWeight: '600',
                      color: theme.text
                    }}>
                      {property.available_rooms}
                    </div>
                    <div style={{
                      fontSize: '0.75rem',
                      color: theme.textSecondary
                    }}>
                      rooms
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {/* View All Properties Link */}
          {todayProperties.length > 0 && (
            <div style={{
              textAlign: 'center',
              paddingTop: '1rem',
              borderTop: `1px solid ${theme.border}`
            }}>
              <button
                style={{
                  backgroundColor: 'transparent',
                  border: 'none',
                  color: currentPalette.primary,
                  fontSize: '0.875rem',
                  cursor: 'pointer',
                  textDecoration: 'underline'
                }}
                onClick={() => {
                  window.location.href = '/history';
                }}
              >
                View all properties in History →
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Analyze;