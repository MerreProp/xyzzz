import React from 'react';

const ProgressTracker = ({ progress, status }) => {
  const steps = [
    { key: 'coordinates', label: 'Extracting coordinates', icon: '📍' },
    { key: 'geocoding', label: 'Getting address details', icon: '🏠' },
    { key: 'property_details', label: 'Fetching property info', icon: '📋' },
    { key: 'scraping', label: 'Analyzing listing data', icon: '🔍' },
    { key: 'excel_export', label: 'Generating report', icon: '📄' }
  ];

  const getStepStatus = (stepKey) => {
    if (!progress || !progress[stepKey]) return 'pending';
    return progress[stepKey];
  };

  const getStepIcon = (stepStatus, defaultIcon) => {
    switch (stepStatus) {
      case 'running':
        return '🔄';
      case 'completed':
        return '✅';
      case 'failed':
        return '❌';
      case 'skipped':
        return '⏭️';
      default:
        return '⏳';
    }
  };

  const getOverallMessage = () => {
    if (status === 'completed') {
      return '🎉 Analysis completed successfully!';
    } else if (status === 'failed') {
      return '❌ Analysis failed. Please try again.';
    } else if (status === 'running') {
      return '🔄 Analyzing property...';
    } else {
      return '⏳ Starting analysis...';
    }
  };

  return (
    <div className="progress-tracker">
      <div className="card-header">
        <h3 className="card-title">{getOverallMessage()}</h3>
        <p className="card-subtitle">
          {status === 'running' && 'This usually takes 30-60 seconds'}
          {status === 'completed' && 'Your property analysis is ready!'}
          {status === 'failed' && 'Something went wrong during the analysis'}
        </p>
      </div>

      <div className="progress-steps">
        {steps.map((step, index) => {
          const stepStatus = getStepStatus(step.key);
          const isActive = stepStatus === 'running';
          
          return (
            <div 
              key={step.key} 
              className={`progress-step ${stepStatus}`}
            >
              <div className={`progress-icon ${stepStatus}`}>
                {isActive ? (
                  <div className="spinner" style={{ width: '16px', height: '16px' }}></div>
                ) : (
                  getStepIcon(stepStatus, step.icon)
                )}
              </div>
              
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: '500', color: '#1e293b' }}>
                  {step.label}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'capitalize' }}>
                  {stepStatus === 'pending' && 'Waiting...'}
                  {stepStatus === 'running' && 'In progress...'}
                  {stepStatus === 'completed' && 'Completed'}
                  {stepStatus === 'failed' && 'Failed'}
                  {stepStatus === 'skipped' && 'Skipped'}
                </div>
              </div>

              <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                {index + 1}/{steps.length}
              </div>
            </div>
          );
        })}
      </div>

      {status === 'running' && (
        <div style={{ 
          marginTop: '1rem', 
          padding: '0.75rem', 
          backgroundColor: '#fef3c7', 
          borderRadius: '6px',
          fontSize: '0.875rem',
          color: '#92400e'
        }}>
          ⚡ Analysis in progress - you can leave this page and come back later
        </div>
      )}
    </div>
  );
};

export default ProgressTracker;