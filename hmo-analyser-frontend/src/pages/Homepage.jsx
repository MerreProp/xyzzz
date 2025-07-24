
import React, { useState, useEffect } from 'react';
import { Search, Database, FileText, Users, MapPin, Calendar, BarChart3, Plus, Clock, CheckCircle, AlertCircle, TrendingUp, Activity } from 'lucide-react';

const HMOInternalDashboard = () => {
  const [healthData, setHealthData] = useState(null);
  const [recentProperties, setRecentProperties] = useState([]);
  const [quickStats, setQuickStats] = useState({});
  const [loading, setLoading] = useState(true);

  // Load real data from your APIs
  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        // Get health/stats data
        const healthResponse = await fetch('/api/health');
        const healthData = await healthResponse.json();
        setHealthData(healthData);

        // Get recent properties (limit to 3 for display)
        const propertiesResponse = await fetch('/api/properties?limit=3');
        const propertiesData = await propertiesResponse.json();
        setRecentProperties(propertiesData);

        // Set empty quick stats (no fake data)
        setQuickStats({
          today_analyses: 0,
          this_week: 0,
          pending_updates: 0,
          export_ready: 0
        });

        setLoading(false);
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
        // Set defaults on error
        setHealthData({
          status: "error",
          total_properties: 0,
          total_analyses: 0,
          active_tasks: 0,
          viable_properties: 0,
          database_connected: false
        });
        setRecentProperties([]);
        setQuickStats({
          today_analyses: 0,
          this_week: 0,
          pending_updates: 0,
          export_ready: 0
        });
        setLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  const AppCard = ({ icon, title, description, onClick, color = "blue", badge }) => {
    const colorMap = {
      blue: { from: '#3b82f6', to: '#1d4ed8' },
      green: { from: '#10b981', to: '#047857' },
      red: { from: '#ef4444', to: '#dc2626' },
      purple: { from: '#8b5cf6', to: '#7c3aed' },
      orange: { from: '#f97316', to: '#ea580c' },
      indigo: { from: '#6366f1', to: '#4f46e5' },
      teal: { from: '#14b8a6', to: '#0f766e' }
    };

    return (
      <div 
        onClick={onClick}
        style={{
          backgroundColor: 'white',
          borderRadius: '16px',
          padding: '24px',
          border: '1px solid #e5e7eb',
          cursor: 'pointer',
          position: 'relative',
          transition: 'all 0.2s ease',
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)'
        }}
        onMouseEnter={(e) => {
          e.target.style.boxShadow = '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)';
          e.target.style.transform = 'scale(1.05)';
        }}
        onMouseLeave={(e) => {
          e.target.style.boxShadow = '0 1px 3px 0 rgba(0, 0, 0, 0.1)';
          e.target.style.transform = 'scale(1)';
        }}
      >
        {badge && (
          <div style={{
            position: 'absolute',
            top: '-8px',
            right: '-8px',
            width: '24px',
            height: '24px',
            backgroundColor: '#ef4444',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <span style={{ color: 'white', fontSize: '12px', fontWeight: '500' }}>{badge}</span>
          </div>
        )}
        <div style={{
          width: '64px',
          height: '64px',
          background: `linear-gradient(to bottom right, ${colorMap[color].from}, ${colorMap[color].to})`,
          borderRadius: '16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          marginBottom: '16px',
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)'
        }}>
          {icon}
        </div>
        <h3 style={{ fontWeight: '600', color: '#111827', marginBottom: '8px', fontSize: '18px' }}>{title}</h3>
        <p style={{ fontSize: '14px', color: '#6b7280', lineHeight: '1.6' }}>{description}</p>
        <div style={{ 
          marginTop: '16px', 
          display: 'flex', 
          alignItems: 'center', 
          fontSize: '12px', 
          color: '#9ca3af',
          transition: 'color 0.2s ease'
        }}>
          <span>Open app</span>
          <svg style={{ width: '12px', height: '12px', marginLeft: '4px' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </div>
      </div>
    );
  };

  const PropertyCard = ({ property }) => (
    <div style={{ 
      backgroundColor: 'white', 
      borderRadius: '8px', 
      padding: '16px', 
      border: '1px solid #e5e7eb', 
      transition: 'box-shadow 0.2s ease',
      cursor: 'pointer'
    }}
    onMouseEnter={(e) => e.target.style.boxShadow = '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)'}
    onMouseLeave={(e) => e.target.style.boxShadow = 'none'}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
        <h3 style={{ fontWeight: '500', color: '#111827', fontSize: '14px', margin: 0 }}>{property.title}</h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {property.status === 'completed' && (
            <CheckCircle style={{ width: '16px', height: '16px', color: '#10b981' }} />
          )}
          {property.status === 'analyzing' && (
            <Clock style={{ width: '16px', height: '16px', color: '#f59e0b' }} />
          )}
          {property.viable === true && (
            <div style={{ 
              padding: '2px 8px', 
              backgroundColor: '#d1fae5', 
              color: '#065f46', 
              fontSize: '12px', 
              borderRadius: '4px' 
            }}>
              Viable
            </div>
          )}
          {property.viable === false && (
            <div style={{ 
              padding: '2px 8px', 
              backgroundColor: '#fee2e2', 
              color: '#991b1b', 
              fontSize: '12px', 
              borderRadius: '4px' 
            }}>
              Not Viable
            </div>
          )}
        </div>
      </div>
      <p style={{ fontSize: '12px', color: '#6b7280', marginBottom: '8px', margin: '8px 0' }}>{property.address}</p>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px', color: '#9ca3af' }}>
        <span>{property.total_rooms} rooms total</span>
        <span>{property.available_rooms} available</span>
        <span>{property.analyzed_date}</span>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Activity className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f9fafb' }}>
      {/* Header */}
      <header style={{ backgroundColor: 'white', borderBottom: '1px solid #e5e7eb' }}>
        <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '0 24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', height: '64px' }}>
            <div>
              <h1 style={{ fontSize: '24px', fontWeight: 'bold', color: '#111827' }}>HMO Analyser</h1>
              <p style={{ fontSize: '14px', color: '#6b7280' }}>Internal Property Analysis Tool</p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              {healthData?.database_connected && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#059669' }}>
                  <CheckCircle style={{ width: '16px', height: '16px' }} />
                  <span style={{ fontSize: '14px' }}>Database Connected</span>
                </div>
              )}
              <button 
                onClick={() => window.location.href = '/analyze'}
                style={{ 
                  padding: '8px 16px', 
                  backgroundColor: '#2563eb', 
                  color: 'white', 
                  borderRadius: '8px', 
                  border: 'none',
                  cursor: 'pointer',
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '8px',
                  fontSize: '14px',
                  transition: 'background-color 0.2s ease'
                }}
                onMouseEnter={(e) => e.target.style.backgroundColor = '#1d4ed8'}
                onMouseLeave={(e) => e.target.style.backgroundColor = '#2563eb'}
              >
                <Plus style={{ width: '16px', height: '16px' }} />
                <span>Analyze Property</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '32px 24px' }}>
        {/* System Status */}
        {healthData?.active_tasks > 0 && (
          <div style={{ 
            backgroundColor: '#eff6ff', 
            border: '1px solid #bfdbfe', 
            borderRadius: '8px', 
            padding: '16px', 
            marginBottom: '24px' 
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Clock style={{ width: '20px', height: '20px', color: '#2563eb' }} />
              <span style={{ fontWeight: '500', color: '#1e3a8a' }}>
                {healthData.active_tasks} analyses currently running
              </span>
            </div>
          </div>
        )}

        {/* Quick Stats */}
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
          gap: '16px', 
          marginBottom: '32px' 
        }}>
          <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '16px', border: '1px solid #e5e7eb' }}>
            <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#111827' }}>{healthData?.total_properties || 0}</div>
            <div style={{ fontSize: '14px', color: '#6b7280' }}>Total Properties</div>
          </div>
          <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '16px', border: '1px solid #e5e7eb' }}>
            <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#059669' }}>{healthData?.viable_properties || 0}</div>
            <div style={{ fontSize: '14px', color: '#6b7280' }}>Viable Properties</div>
          </div>
          <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '16px', border: '1px solid #e5e7eb' }}>
            <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#2563eb' }}>{quickStats.this_week || '-'}</div>
            <div style={{ fontSize: '14px', color: '#6b7280' }}>This Week</div>
          </div>
          <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '16px', border: '1px solid #e5e7eb' }}>
            <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#7c3aed' }}>{quickStats.export_ready || '-'}</div>
            <div style={{ fontSize: '14px', color: '#6b7280' }}>Ready to Export</div>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* App Grid */}
          <div className="lg:col-span-2">
            <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
              <div className="w-2 h-6 bg-blue-600 rounded-full mr-3"></div>
              Applications
            </h2>
            <div className="grid grid-cols-2 gap-6 mb-8">
              <AppCard
                icon={<Search className="w-8 h-8" />}
                title="Property Analyzer"
                description="Start new analysis of SpareRoom listings with automated data extraction"
                color="blue"
                onClick={() => window.location.href = '/analyze'}
              />
              <AppCard
                icon={<Database className="w-8 h-8" />}
                title="Property Database"
                description="Browse, search and manage all analyzed properties with advanced filters"
                color="green"
                onClick={() => window.location.href = '/history'}
              />
              <AppCard
                icon={<MapPin className="w-8 h-8" />}
                title="Property Map"
                description="Interactive map view of all analyzed properties with location-based insights"
                color="red"
                onClick={() => window.location.href = '/map'}
              />
              <AppCard
                icon={<Users className="w-8 h-8" />}
                title="Advertiser Profiles"
                description="View landlord portfolios, track performance and analyze market trends"
                color="purple"
                onClick={() => window.location.href = '/advertisers'}
              />
              <AppCard
                icon={<BarChart3 className="w-8 h-8" />}
                title="Analytics Suite"
                description="Advanced analytics dashboard with availability tracking and insights"
                color="orange"
                badge={quickStats.pending_updates > 0 ? quickStats.pending_updates : null}
                onClick={() => window.location.href = '/analytics'}
              />
              <AppCard
                icon={<Calendar className="w-8 h-8" />}
                title="Availability Tracker"
                description="Monitor room availability patterns with interactive heatmaps and calendars"
                color="indigo"
                onClick={() => window.location.href = '/availability'}
              />
              <AppCard
                icon={<FileText className="w-8 h-8" />}
                title="Export Manager"
                description="Generate and manage Excel reports, bulk exports and custom data views"
                color="teal"
                badge={quickStats.export_ready > 0 ? quickStats.export_ready : null}
                onClick={() => window.location.href = '/exports'}
              />
            </div>

            {/* Recent Properties */}
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Analyses</h2>
            <div className="space-y-3">
              {recentProperties.map((property) => (
                <PropertyCard key={property.property_id} property={property} />
              ))}
            </div>
          </div>

          {/* Sidebar */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* System Info */}
            <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '24px', border: '1px solid #e5e7eb' }}>
              <h3 style={{ fontWeight: '600', color: '#111827', marginBottom: '16px' }}>System Status</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '14px', color: '#6b7280' }}>Database</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#059669' }}>
                    <CheckCircle style={{ width: '16px', height: '16px' }} />
                    <span style={{ fontSize: '14px' }}>Connected</span>
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '14px', color: '#6b7280' }}>Active Tasks</span>
                  <span style={{ fontSize: '14px', fontWeight: '500' }}>{healthData?.active_tasks || 0}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '14px', color: '#6b7280' }}>Pending Updates</span>
                  <span style={{ fontSize: '14px', fontWeight: '500' }}>{quickStats.pending_updates || 0}</span>
                </div>
              </div>
            </div>

            {/* Today's Activity */}
            <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '24px', border: '1px solid #e5e7eb' }}>
              <h3 style={{ fontWeight: '600', color: '#111827', marginBottom: '16px' }}>Today's Activity</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '14px', color: '#6b7280' }}>New Analyses</span>
                  <span style={{ fontSize: '14px', fontWeight: '500' }}>-</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '14px', color: '#6b7280' }}>Exports Generated</span>
                  <span style={{ fontSize: '14px', fontWeight: '500' }}>-</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '14px', color: '#6b7280' }}>Properties Updated</span>
                  <span style={{ fontSize: '14px', fontWeight: '500' }}>-</span>
                </div>
              </div>
            </div>

            {/* Quick Tools */}
            <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '24px', border: '1px solid #e5e7eb' }}>
              <h3 style={{ fontWeight: '600', color: '#111827', marginBottom: '16px' }}>Quick Tools</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <button style={{ 
                  width: '100%', 
                  textAlign: 'left', 
                  padding: '12px', 
                  fontSize: '14px', 
                  color: '#374151', 
                  backgroundColor: 'transparent',
                  border: 'none',
                  borderRadius: '4px', 
                  cursor: 'pointer',
                  transition: 'background-color 0.2s ease'
                }}
                onMouseEnter={(e) => e.target.style.backgroundColor = '#f9fafb'}
                onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}>
                  🔄 Update All Properties
                </button>
                <button style={{ 
                  width: '100%', 
                  textAlign: 'left', 
                  padding: '12px', 
                  fontSize: '14px', 
                  color: '#374151', 
                  backgroundColor: 'transparent',
                  border: 'none',
                  borderRadius: '4px', 
                  cursor: 'pointer',
                  transition: 'background-color 0.2s ease'
                }}
                onMouseEnter={(e) => e.target.style.backgroundColor = '#f9fafb'}
                onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}>
                  📊 Export Summary Report
                </button>
                <button style={{ 
                  width: '100%', 
                  textAlign: 'left', 
                  padding: '12px', 
                  fontSize: '14px', 
                  color: '#374151', 
                  backgroundColor: 'transparent',
                  border: 'none',
                  borderRadius: '4px', 
                  cursor: 'pointer',
                  transition: 'background-color 0.2s ease'
                }}
                onMouseEnter={(e) => e.target.style.backgroundColor = '#f9fafb'}
                onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}>
                  🗂️ Manage Export Files
                </button>
                <button style={{ 
                  width: '100%', 
                  textAlign: 'left', 
                  padding: '12px', 
                  fontSize: '14px', 
                  color: '#374151', 
                  backgroundColor: 'transparent',
                  border: 'none',
                  borderRadius: '4px', 
                  cursor: 'pointer',
                  transition: 'background-color 0.2s ease'
                }}
                onMouseEnter={(e) => e.target.style.backgroundColor = '#f9fafb'}
                onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}>
                  ⚙️ System Settings
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HMOInternalDashboard;