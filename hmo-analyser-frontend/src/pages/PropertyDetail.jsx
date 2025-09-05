import React, { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import ResultsCard from '../components/ResultsCard';
import { propertyApi } from '../utils/api';
import Phase2Analytics from '../components/Phase2Analytics';
import Phase3Analytics from '../components/Phase3Analytics';
import AvailabilityHeatmap from '../components/AvailabilityHeatmap';

const PropertyDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showChanges, setShowChanges] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // Fetch property details
  const { data: property, isLoading, error } = useQuery({
    queryKey: ['property', id],
    queryFn: () => propertyApi.getPropertyDetails(id),
  });

  // Fetch property changes
  const { data: changes = [], isLoading: changesLoading } = useQuery({
    queryKey: ['property-changes', id],
    queryFn: async () => {
      try {
        const response = await fetch(`/api/properties/${id}/changes`);
        if (!response.ok) {
          throw new Error('Failed to fetch changes');
        }
        return response.json();
      } catch (error) {
        console.error('Error fetching changes:', error);
        return [];
      }
    },
    enabled: showChanges
  });

  // Handle delete property
  const handleDeleteProperty = async () => {
    const confirmDelete = window.confirm(
      '⚠️ Are you sure you want to delete this property?\n\n' +
      'This will permanently remove:\n' +
      '• All property analysis data\n' +
      '• Price history and trends\n' +
      '• Room availability records\n' +
      '• Associated Excel files\n\n' +
      'This action cannot be undone!'
    );

    if (!confirmDelete) return;

    // Double confirmation for safety
    const doubleConfirm = window.confirm(
      '🚨 FINAL CONFIRMATION\n\n' +
      'You are about to permanently delete this property and ALL its data.\n\n' +
      'Type "DELETE" in the next dialog to confirm, or click Cancel to abort.'
    );

    if (!doubleConfirm) return;

    const userInput = prompt(
      'Please type "DELETE" (in capital letters) to confirm deletion:'
    );

    if (userInput !== 'DELETE') {
      alert('Deletion cancelled. You must type "DELETE" exactly to confirm.');
      return;
    }

    setIsDeleting(true);

    try {
      await propertyApi.deleteAnalysis(id);
      
      // Show success message
      alert('✅ Property deleted successfully!');
      
      // ADDED: Cache invalidation before navigation
      await queryClient.invalidateQueries({ queryKey: ['properties'] }); // History page query
      await queryClient.invalidateQueries({ queryKey: ['property'] }); // Individual property queries
      
      // ADDED: Remove the specific property from cache immediately
      queryClient.removeQueries({ queryKey: ['property', id] });
      
      // Navigate back to history page
      navigate('/history');
      
    } catch (error) {
      console.error('Failed to delete property:', error);
      alert('❌ Failed to delete property. Please try again or contact support.');
    } finally {
      setIsDeleting(false);
    }
  };


  // ADD this to PropertyDetail.jsx - add these to the component state and functions:

  const [isUpdating, setIsUpdating] = useState(false);
  const [updateTaskId, setUpdateTaskId] = useState(null);

  // ADD this function alongside handleDeleteProperty:
  const handleUpdateProperty = async () => {
    const confirmUpdate = window.confirm(
      '🔄 Update Property Analysis?\n\n' +
      'This will:\n' +
      '• Re-analyze the property for changes\n' +
      '• Check for new room availability\n' +
      '• Update pricing information\n' +
      '• Track any changes detected\n\n' +
      'Continue with property update?'
    );

    if (!confirmUpdate) return;

    setIsUpdating(true);

    try {
      // Call the update API endpoint
      const response = await fetch(`/api/properties/${id}/update`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to start property update');
      }

      const result = await response.json();
      setUpdateTaskId(result.task_id);
      
      alert('✅ Property update started!\n\nThe analysis is running in the background. Refresh the page in a few moments to see any changes.');
      
      // CHANGED: Added cache invalidation
      setTimeout(async () => {
        await queryClient.invalidateQueries({ queryKey: ['properties'] });
        await queryClient.invalidateQueries({ queryKey: ['property', id] });
        window.location.reload();
      }, 3000);
      
    } catch (error) {
      console.error('Failed to update property:', error);
      alert('❌ Failed to start property update. Please try again.');
    } finally {
      setIsUpdating(false);
    }
  };

  const formatDate = (dateString) => {
    try {
      return new Date(dateString).toLocaleString('en-GB', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (error) {
      return 'Invalid Date';
    }
  };

  const getChangeIcon = (changeType) => {
    switch (changeType) {
      case 'status': return '📊';
      case 'price': return '💰';
      case 'availability': return '🏠';
      case 'rooms': return '🛏️';
      case 'bills': return '💡';
      case 'requirements': return '✅';
      default: return '📝';
    }
  };

  const getChangeColor = (changeType) => {
    switch (changeType) {
      case 'status': return { bg: '#fef3c7', border: '#f59e0b' };
      case 'price': return { bg: '#dcfce7', border: '#16a34a' };
      case 'availability': return { bg: '#dbeafe', border: '#2563eb' };
      case 'rooms': return { bg: '#fed7aa', border: '#ea580c' };
      case 'bills': return { bg: '#fce7f3', border: '#ec4899' };
      case 'requirements': return { bg: '#e0e7ff', border: '#6366f1' };
      default: return { bg: '#f1f5f9', border: '#64748b' };
    }
  };

  // Add this helper function here
  const getDateGoneDisplay = (dateGone) => {
    if (!dateGone) return '—';
    
    try {
      // Handle different date formats
      const date = new Date(dateGone);
      const now = new Date();
      const daysDiff = Math.floor((now - date) / (1000 * 60 * 60 * 24));
      
      const formattedDate = date.toLocaleDateString('en-GB', {
        day: '2-digit',
        month: '2-digit',
        year: '2-digit'
      });
      
      // Add "days ago" indicator for recent dates
      if (daysDiff <= 30) {
        return (
          <div>
            <div style={{ fontSize: '0.875rem' }}>{formattedDate}</div>
            <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
              {daysDiff === 0 ? 'Today' : 
               daysDiff === 1 ? 'Yesterday' : 
               `${daysDiff} days ago`}
            </div>
          </div>
        );
      }
      
      return formattedDate;
    } catch (error) {
      return dateGone;
    }
  };

  if (isLoading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <div style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>🔄 Loading Property Details...</div>
        <div className="spinner"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <h2 className="card-title">❌ Error Loading Property</h2>
        <p style={{ color: '#dc2626', marginBottom: '1rem' }}>
          {error.message || 'Failed to load property details.'} 
          The property may have been deleted or there was a connection error.
        </p>
        <Link to="/history" className="btn btn-primary">
          ← Back to History
        </Link>
      </div>
    );
  }

  if (!property) {
    return (
      <div className="card">
        <h2 className="card-title">📭 Property Not Found</h2>
        <p style={{ color: '#64748b', marginBottom: '1rem' }}>
          The requested property could not be found.
        </p>
        <Link to="/history" className="btn btn-primary">
          ← Back to History
        </Link>
      </div>
    );
  }

  // Add safety check for property data
  const safeProperty = property || {};
  
  return (
    <div>
      {/* Header with navigation and actions */}
      <div style={{ 
        marginBottom: '2rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        flexWrap: 'wrap',
        gap: '1rem'
      }}>
        <div style={{ flex: 1, minWidth: '300px' }}>
          <Link 
            to="/history" 
            style={{ 
              color: '#667eea', 
              textDecoration: 'none',
              fontSize: '0.875rem',
              marginBottom: '0.5rem',
              display: 'block'
            }}
          >
            ← Back to History
          </Link>
          <h1 style={{ fontSize: '2rem', fontWeight: 'bold', color: '#1e293b', margin: 0 }}>
            Property Details
          </h1>
          
          {/* Add advertiser link if available */}
          {safeProperty['Advertiser Name'] && (
            <div style={{ marginTop: '0.5rem' }}>
              <Link 
                to={`/advertiser/${encodeURIComponent(safeProperty['Advertiser Name'])}`}
                style={{ 
                  color: '#667eea', 
                  textDecoration: 'none',
                  fontSize: '0.875rem',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.25rem'
                }}
              >
                🏢 View all properties by {safeProperty['Advertiser Name']}
              </Link>
            </div>
          )}
        </div>
        
        {/* Action buttons */}
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          {/* Update button - NEW */}
          <button
            onClick={handleUpdateProperty}
            disabled={isUpdating}
            style={{
              padding: '0.75rem 1.5rem',
              background: isUpdating ? '#9ca3af' : 'linear-gradient(135deg, #059669 0%, #047857 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: isUpdating ? 'not-allowed' : 'pointer',
              fontSize: '0.875rem',
              fontWeight: '500',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              transition: 'all 0.2s ease',
              boxShadow: isUpdating ? 'none' : '0 2px 4px rgba(5, 150, 105, 0.2)',
            }}
            onMouseEnter={(e) => {
              if (!isUpdating) {
                e.target.style.transform = 'translateY(-1px)';
                e.target.style.boxShadow = '0 4px 12px rgba(5, 150, 105, 0.3)';
              }
            }}
            onMouseLeave={(e) => {
              if (!isUpdating) {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 2px 4px rgba(5, 150, 105, 0.2)';
              }
            }}
          >
            {isUpdating ? (
              <>
                <div className="spinner" style={{ width: '16px', height: '16px' }}></div>
                Updating...
              </>
            ) : (
              <>
                🔄 Update Property
              </>
            )}
          </button>

          <button
            onClick={() => setShowChanges(!showChanges)}
            className="btn btn-secondary"
            style={{
              backgroundColor: showChanges ? '#667eea' : '#f1f5f9',
              color: showChanges ? 'white' : '#64748b'
            }}
          >
            📈 {showChanges ? 'Hide Changes' : 'Show Changes'}
          </button>

          {/* Delete button */}
          <button
            onClick={handleDeleteProperty}
            disabled={isDeleting}
            style={{
              padding: '0.75rem 1.5rem',
              background: isDeleting ? '#9ca3af' : 'linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: isDeleting ? 'not-allowed' : 'pointer',
              fontSize: '0.875rem',
              fontWeight: '500',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              transition: 'all 0.2s ease',
              boxShadow: isDeleting ? 'none' : '0 2px 4px rgba(220, 38, 38, 0.2)',
            }}
            onMouseEnter={(e) => {
              if (!isDeleting) {
                e.target.style.transform = 'translateY(-1px)';
                e.target.style.boxShadow = '0 4px 12px rgba(220, 38, 38, 0.3)';
              }
            }}
            onMouseLeave={(e) => {
              if (!isDeleting) {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 2px 4px rgba(220, 38, 38, 0.2)';
              }
            }}
          >
            {isDeleting ? (
              <>
                <div className="spinner" style={{ width: '16px', height: '16px' }}></div>
                Deleting...
              </>
            ) : (
              <>
                🗑️ Delete Property
              </>
            )}
          </button>
        </div>
      </div>

      {/* Property summary card */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <div className="card-header">
          <h2 className="card-title">📋 Property Summary</h2>
          <p className="card-subtitle">
            Analyzed on {formatDate(safeProperty['Analysis Date'])}
          </p>
        </div>
        
        <ResultsCard 
          property={safeProperty} 
          taskId={id}
        />
      </div>

      {/* Availability Summary */}
      {safeProperty['Availability Summary'] && (
        <div className="card" style={{ marginBottom: '2rem' }}>
          <h3 className="card-title">📊 Availability Summary</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
            
            <div style={{ padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '8px' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#059669' }}>
                {safeProperty['Availability Summary'].current_available_rooms}
              </div>
              <div style={{ fontSize: '0.875rem', color: '#64748b' }}>
                Currently Available
              </div>
            </div>
            
            <div style={{ padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '8px' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#dc2626' }}>
                {safeProperty['Availability Summary'].rooms_gone}
              </div>
              <div style={{ fontSize: '0.875rem', color: '#64748b' }}>
                Rooms Gone
              </div>
            </div>
            
            <div style={{ padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '8px' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#ea580c' }}>
                {safeProperty['Availability Summary'].availability_changes}
              </div>
              <div style={{ fontSize: '0.875rem', color: '#64748b' }}>
                Availability Changes
              </div>
            </div>
            
            <div style={{ padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '8px' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#7c3aed' }}>
                {Math.round(safeProperty['Availability Summary'].average_occupancy_rate)}%
              </div>
              <div style={{ fontSize: '0.875rem', color: '#64748b' }}>
                Avg Occupancy Rate
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Changes section */}
      {showChanges && (
        <div className="card" style={{ marginBottom: '2rem' }}>
          <h3 className="card-title">📈 Property Changes</h3>
          
          {changesLoading ? (
            <div style={{ textAlign: 'center', padding: '2rem' }}>
              <div className="spinner"></div>
              <p>Loading changes...</p>
            </div>
          ) : changes.length === 0 ? (
            <div style={{ 
              textAlign: 'center', 
              padding: '2rem',
              backgroundColor: '#f8fafc',
              borderRadius: '8px',
              border: '1px dashed #cbd5e1'
            }}>
              <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>📊</div>
              <h4 style={{ color: '#64748b', marginBottom: '0.5rem' }}>No Changes Detected</h4>
              <p style={{ color: '#64748b', fontSize: '0.875rem' }}>
                This property hasn't had any tracked changes yet. Changes will appear here when the property is re-analyzed and differences are detected.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {changes.map((change, index) => {
                const colors = getChangeColor(change.change_type);
                return (
                  <div
                    key={index}
                    style={{
                      padding: '1rem',
                      backgroundColor: colors.bg,
                      border: `2px solid ${colors.border}`,
                      borderRadius: '8px'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                      <span style={{ fontSize: '1.25rem' }}>{getChangeIcon(change.change_type)}</span>
                      <strong style={{ color: '#1e293b' }}>{change.change_summary}</strong>
                      <span style={{ fontSize: '0.75rem', color: '#64748b', marginLeft: 'auto' }}>
                        {formatDate(change.detected_at)}
                      </span>
                    </div>
                    
                    <div style={{ fontSize: '0.875rem', color: '#374151' }}>
                      <strong>Field:</strong> {change.field_name}
                    </div>
                    
                    {change.old_value && (
                      <div style={{ fontSize: '0.875rem', color: '#374151', marginTop: '0.25rem' }}>
                        <strong>From:</strong> {change.old_value} → <strong>To:</strong> {change.new_value}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Phase 2 Analytics */}
      <Phase2Analytics propertyId={id} />

      {/* Phase 3 Analytics */}
      <Phase3Analytics propertyId={id} />

      {/* Availability Heatmap */}
      <AvailabilityHeatmap propertyId={id} />

      {/* Additional Analysis Information */}
      <div className="card" style={{ marginTop: '2rem' }}>
        <h3 className="card-title">📊 Analysis Information</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          
          <div>
            <div style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '0.25rem' }}>
              Date Found
            </div>
            <div style={{ fontWeight: '500' }}>
              {safeProperty['Date Found'] || safeProperty['Analysis Date'] || 'N/A'}
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '0.25rem' }}>
              Analysis Date
            </div>
            <div style={{ fontWeight: '500' }}>
              {safeProperty['Analysis Date'] || 'N/A'}
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '0.25rem' }}>
              Property ID
            </div>
            <div style={{ fontWeight: '500' }}>
              {safeProperty['Property ID'] || id}
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '0.25rem' }}>
              Analysis Status
            </div>
            <div style={{ fontWeight: '500', color: '#059669' }}>
              ✅ Completed
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '0.25rem' }}>
              Updates Tracked
            </div>
            <div style={{ fontWeight: '500' }}>
              {changes.length} changes
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '0.25rem' }}>
              Source URL
            </div>
            <div>
              {safeProperty['URL'] ? (
                <a 
                  href={safeProperty['URL']} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  style={{ 
                    color: '#667eea', 
                    textDecoration: 'none',
                    fontSize: '0.875rem'
                  }}
                >
                  🔗 View Original Listing
                </a>
              ) : (
                <span style={{ fontSize: '0.875rem', color: '#64748b' }}>N/A</span>
              )}
            </div>
          </div>

          {/* Add advertiser info section */}
          {safeProperty['Advertiser Name'] && (
            <div>
              <div style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '0.25rem' }}>
                Advertiser
              </div>
              <div>
                <Link 
                  to={`/advertiser/${encodeURIComponent(safeProperty['Advertiser Name'])}`}
                  style={{ 
                    color: '#667eea', 
                    textDecoration: 'none',
                    fontSize: '0.875rem',
                    fontWeight: '500'
                  }}
                >
                  🏢 {safeProperty['Advertiser Name']}
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Navigation Footer */}
      <div style={{ 
        marginTop: '2rem', 
        padding: '1rem', 
        backgroundColor: '#f8fafc', 
        borderRadius: '8px',
        textAlign: 'center'
      }}>
        <p style={{ fontSize: '0.875rem', color: '#64748b', margin: 0 }}>
          💡 Use the "Delete Property" button above to permanently remove this property, or visit the{' '}
          <Link to="/history" style={{ color: '#667eea' }}>History page</Link>{' '}
          to compare with other properties and run updates to track changes.
          {safeProperty['Advertiser Name'] && (
            <>
              {' '}You can also view{' '}
              <Link to={`/advertiser/${encodeURIComponent(safeProperty['Advertiser Name'])}`} style={{ color: '#667eea' }}>
                all properties by {safeProperty['Advertiser Name']}
              </Link>.
            </>
          )}
        </p>
      </div>
    </div>
  );
};

export default PropertyDetail;