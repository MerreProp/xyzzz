// Analyze.jsx - Updated with Last Property Summary and FIXED API endpoints

import React, { useState, useEffect } from 'react';
import PropertyForm from '../components/PropertyForm';
import ProgressTracker from '../components/ProgressTracker';
import ResultsCard from '../components/ResultsCard';
import LastPropertySummary from '../components/LastPropertySummary';
import DuplicatePropertyModal from '../components/DuplicatePropertyModal';

const Analyze = () => {
  const [currentAnalysis, setCurrentAnalysis] = useState(null);
  const [analysisStatus, setAnalysisStatus] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [healthData, setHealthData] = useState(null);
  const [analysisError, setAnalysisError] = useState(null);
  
  // Duplicate detection state
  const [duplicateData, setDuplicateData] = useState(null);
  const [showDuplicateModal, setShowDuplicateModal] = useState(false);
  const [currentUrl, setCurrentUrl] = useState('');

  // Health check on component mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch('/api/health');
        const data = await response.json();
        setHealthData(data);
      } catch (error) {
        console.error('Health check failed:', error);
      }
    };
    checkHealth();
  }, []);

  // FIXED: Handle analyze property with proper duplicate detection
  const handleAnalyzeProperty = async (url) => {
    try {
      console.log('Starting analysis for:', url);
      
      setAnalysisError(null);
      setAnalysisResult(null);
      setCurrentUrl(url);
      
      // FIXED: Use the correct API endpoint
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

      // FIXED: Handle duplicate detection response
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
    }
  };

  // FIXED: Use correct API endpoint for polling status
  const pollAnalysisStatus = async (taskId) => {
    const maxAttempts = 60;
    let attempts = 0;

    const poll = async () => {
      try {
        attempts++;
        // FIXED: Use the correct API endpoint
        const response = await fetch(`/api/analysis/${taskId}`);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const status = await response.json();
        setAnalysisStatus(status);

        if (status.status === 'completed') {
          setAnalysisResult(status.result);
          setCurrentAnalysis(null);
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

  // Handle duplicate modal actions
  const handleLinkToExisting = async () => {
    if (!duplicateData?.potential_matches?.[0]) return;

    try {
      const match = duplicateData.potential_matches[0];
      
      // Link URL to existing property
      const response = await fetch(`/api/properties/${match.property_id}/link-url`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ new_url: currentUrl }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to link property');
      }
      
      setShowDuplicateModal(false);
      setDuplicateData(null);
      
      // Start analysis on the existing property
      handleAnalyzeProperty(currentUrl);
      
    } catch (error) {
      console.error('Failed to link property:', error);
      setAnalysisError('Failed to link property. Please try again.');
    }
  };

  const handleCreateSeparate = () => {
    setShowDuplicateModal(false);
    setDuplicateData(null);
    
    // Force create as separate property
    handleAnalyzePropertyForced(currentUrl);
  };

  const handleAnalyzePropertyForced = async (url) => {
    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url, force_separate: true }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setCurrentAnalysis(result.task_id);
      setAnalysisStatus(result);
      pollAnalysisStatus(result.task_id);

    } catch (error) {
      console.error('Failed to analyze property:', error);
      setAnalysisError(error.message);
    }
  };

  const isAnalyzing = !!currentAnalysis;

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem' }}>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#1e293b', marginBottom: '0.5rem' }}>
          🔍 Property Analyzer
        </h1>
        <p style={{ color: '#64748b', fontSize: '1.1rem' }}>
          Analyze SpareRoom properties for HMO investment potential
        </p>
      </div>

      {/* Health Status Banner */}
      {healthData && (
        <div style={{ 
          padding: '1rem',
          backgroundColor: '#dcfce7',
          border: '1px solid #16a34a',
          borderRadius: '8px',
          marginBottom: '2rem',
          fontSize: '0.875rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ color: '#16a34a', fontWeight: '500' }}>✅ System Status:</span>
            <span style={{ color: '#374151' }}>
              {healthData.total_properties} properties analyzed • 
              {healthData.viable_properties} viable • 
              {healthData.active_tasks} active tasks
            </span>
            <button
              onClick={() => setHealthData(null)}
              style={{
                marginLeft: 'auto',
                background: 'none',
                border: 'none',
                fontSize: '1.25rem',
                cursor: 'pointer',
                color: 'inherit',
                opacity: 0.7
              }}
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Enhanced Property Form */}
      <PropertyForm 
        onSubmit={handleAnalyzeProperty}
        isLoading={isAnalyzing}
        analysisResult={analysisResult}
        analysisError={analysisError}
      />

      {/* Progress Tracker */}
      {currentAnalysis && (
        <ProgressTracker 
          progress={analysisStatus?.progress}
          status={analysisStatus?.status || 'pending'}
        />
      )}

      {/* Results Display */}
      {analysisResult && (
        <ResultsCard 
          property={analysisResult}
          taskId={analysisStatus?.task_id}
        />
      )}

      {/* Last Property Summary - Show when not currently analyzing */}
      {!currentAnalysis && !analysisResult && (
        <LastPropertySummary />
      )}

      {/* Getting Started Guide - Only show if no results and no last property */}
      {!currentAnalysis && !analysisResult && !analysisError && (
        <div className="card" style={{ marginTop: '2rem' }}>
          <div className="card-header">
            <h3 className="card-title">🚀 Getting Started</h3>
            <p className="card-subtitle">
              Follow these steps to analyze your first property
            </p>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
            <div>
              <div style={{ 
                backgroundColor: '#f0f9ff', 
                padding: '1rem', 
                borderRadius: '8px',
                border: '1px solid #0ea5e9'
              }}>
                <h4 style={{ color: '#0369a1', marginBottom: '0.5rem' }}>
                  1️⃣ Find a Property
                </h4>
                <p style={{ fontSize: '0.875rem', color: '#374151', marginBottom: '0.5rem' }}>
                  Go to SpareRoom.co.uk and find an HMO property you're interested in.
                </p>
                <a 
                  href="https://www.spareroom.co.uk/flatshare/" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  style={{ 
                    fontSize: '0.875rem', 
                    color: '#0369a1', 
                    textDecoration: 'none',
                    fontWeight: '500'
                  }}
                >
                  🔗 Visit SpareRoom →
                </a>
              </div>
            </div>

            <div>
              <div style={{ 
                backgroundColor: '#f0fdf4', 
                padding: '1rem', 
                borderRadius: '8px',
                border: '1px solid #22c55e'
              }}>
                <h4 style={{ color: '#16a34a', marginBottom: '0.5rem' }}>
                  2️⃣ Copy the URL
                </h4>
                <p style={{ fontSize: '0.875rem', color: '#374151', marginBottom: '0.5rem' }}>
                  Copy the full URL from your browser's address bar.
                </p>
                <p style={{ fontSize: '0.75rem', color: '#64748b' }}>
                  Example: https://www.spareroom.co.uk/flatshare/flatshare_detail.pl?...
                </p>
              </div>
            </div>

            <div>
              <div style={{ 
                backgroundColor: '#fefce8', 
                padding: '1rem', 
                borderRadius: '8px',
                border: '1px solid #eab308'
              }}>
                <h4 style={{ color: '#ca8a04', marginBottom: '0.5rem' }}>
                  3️⃣ Analyze & Review
                </h4>
                <p style={{ fontSize: '0.875rem', color: '#374151', marginBottom: '0.5rem' }}>
                  Paste the URL above and get instant HMO viability analysis.
                </p>
                <p style={{ fontSize: '0.75rem', color: '#64748b' }}>
                  Results include income potential, room breakdown, and investment insights.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Error Display */}
      {analysisError && (
        <div className="card" style={{ 
          marginTop: '2rem',
          border: '1px solid #dc2626',
          backgroundColor: '#fef2f2'
        }}>
          <div className="card-header">
            <h3 className="card-title" style={{ color: '#dc2626' }}>
              ❌ Analysis Failed
            </h3>
          </div>
          <p style={{ color: '#7f1d1d', marginBottom: '1rem' }}>
            {analysisError}
          </p>
          <button 
            onClick={() => setAnalysisError(null)}
            className="btn btn-secondary"
            style={{ fontSize: '0.875rem' }}
          >
            Try Again
          </button>
        </div>
      )}

      {/* Duplicate Detection Modal */}
      {showDuplicateModal && duplicateData && (
        <DuplicatePropertyModal
          duplicateData={duplicateData}
          onLinkToExisting={handleLinkToExisting}
          onCreateSeparate={handleCreateSeparate}
          onCancel={() => {
            setShowDuplicateModal(false);
            setDuplicateData(null);
          }}
          isLinking={false}
        />
      )}
    </div>
  );
};

export default Analyze;