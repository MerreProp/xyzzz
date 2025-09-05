// src/pages/Settings.jsx
import React, { useState } from 'react';
import { Settings, Palette, Monitor, User, Bell, Shield, Database, Activity, CheckCircle, AlertCircle, Moon, Sun } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { useDarkMode } from '../contexts/DarkModeContext';

const SettingsPage = () => {
  // Get theme and dark mode from contexts
  const { activeColorTheme, setColorTheme, colorPalettes, currentPalette } = useTheme();
  const { isDarkMode, toggleDarkMode } = useDarkMode();
  const [activeTab, setActiveTab] = useState('appearance');

  // Base colors for consistent theming
  const baseColors = {
    darkSlate: '#2C3E4A',
    lightCream: '#F5F1E8',
    softGray: '#A8A5A0',
  };

  // Theme configuration based on dark mode and current palette
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

  // Mock system status data
  const systemStatus = {
    database: { status: 'online', message: 'Database Connected' },
    api: { status: 'online', message: 'API Services Running' },
    storage: { status: 'online', message: 'Storage Available' },
    lastBackup: '2 hours ago'
  };

  const tabs = [
    { id: 'appearance', label: 'Appearance', icon: Palette },
    { id: 'system', label: 'System Status', icon: Monitor },
    { id: 'account', label: 'Account', icon: User },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'security', label: 'Security', icon: Shield }
  ];

  // Color theme change handler
  const handleColorThemeChange = (themeKey) => {
    setColorTheme(themeKey);
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: theme.mainBg,
      padding: '2rem',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      transition: 'background-color 0.3s ease'
    }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '2rem' }}>
          <h1 style={{
            fontSize: '2rem',
            fontWeight: '700',
            color: theme.text,
            marginBottom: '0.5rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem'
          }}>
            <Settings size={32} style={{ color: currentPalette.primary }} />
            Settings
          </h1>
          <p style={{
            fontSize: '1rem',
            color: theme.textSecondary,
            margin: 0
          }}>
            Customize your HMO Analyser experience
          </p>
        </div>

        {/* Tab Navigation */}
        <div style={{
          display: 'flex',
          gap: '0.5rem',
          marginBottom: '2rem',
          overflowX: 'auto',
          paddingBottom: '0.5rem'
        }}>
          {tabs.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.75rem 1.5rem',
                backgroundColor: activeTab === id ? currentPalette.primary : theme.cardBg,
                color: activeTab === id ? 'white' : theme.text,
                border: `1px solid ${activeTab === id ? currentPalette.primary : theme.border}`,
                borderRadius: '12px',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: '500',
                transition: 'all 0.2s ease',
                whiteSpace: 'nowrap'
              }}
              onMouseEnter={(e) => {
                if (activeTab !== id) {
                  e.currentTarget.style.backgroundColor = `rgba(${currentPalette.primary.slice(1).match(/.{2}/g).map(hex => parseInt(hex, 16)).join(', ')}, 0.1)`;
                }
              }}
              onMouseLeave={(e) => {
                if (activeTab !== id) {
                  e.currentTarget.style.backgroundColor = theme.cardBg;
                }
              }}
            >
              <Icon size={16} />
              {label}
            </button>
          ))}
        </div>

        {/* Content Area */}
        <div style={{
          backgroundColor: theme.cardBg,
          borderRadius: '16px',
          padding: '2rem',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
          border: `1px solid ${theme.border}`,
          transition: 'all 0.3s ease'
        }}>
          {/* Appearance Tab */}
          {activeTab === 'appearance' && (
            <div>
              <h2 style={{
                fontSize: '1.5rem',
                fontWeight: '600',
                color: theme.text,
                marginBottom: '1.5rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                <Palette size={24} style={{ color: currentPalette.primary }} />
                Appearance Settings
              </h2>

              {/* Dark Mode Toggle */}
              <div style={{
                padding: '1.5rem',
                backgroundColor: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)',
                borderRadius: '12px',
                marginBottom: '2rem'
              }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div>
                    <h3 style={{
                      fontSize: '1.125rem',
                      fontWeight: '600',
                      color: theme.text,
                      marginBottom: '0.25rem'
                    }}>
                      Dark Mode
                    </h3>
                    <p style={{
                      fontSize: '0.875rem',
                      color: theme.textSecondary,
                      margin: 0
                    }}>
                      Switch between light and dark themes
                    </p>
                  </div>
                  <button
                    onClick={toggleDarkMode}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      padding: '0.75rem 1rem',
                      backgroundColor: currentPalette.primary,
                      color: 'white',
                      border: 'none',
                      borderRadius: '10px',
                      cursor: 'pointer',
                      fontSize: '0.875rem',
                      fontWeight: '500',
                      transition: 'all 0.2s ease'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = currentPalette.secondary;
                      e.currentTarget.style.transform = 'translateY(-1px)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = currentPalette.primary;
                      e.currentTarget.style.transform = 'translateY(0)';
                    }}
                  >
                    {isDarkMode ? <Sun size={16} /> : <Moon size={16} />}
                    {isDarkMode ? 'Switch to Light' : 'Switch to Dark'}
                  </button>
                </div>
              </div>

              {/* Color Palette Switcher */}
              <div>
                <h3 style={{
                  fontSize: '1.125rem',
                  fontWeight: '600',
                  color: theme.text,
                  marginBottom: '1rem'
                }}>
                  Color Theme
                </h3>
                <p style={{
                  fontSize: '0.875rem',
                  color: theme.textSecondary,
                  marginBottom: '1.5rem'
                }}>
                  Choose from our earthy color palette inspired by natural artwork
                </p>
                
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minMax(200px, 1fr))',
                  gap: '1rem'
                }}>
                  {Object.entries(colorPalettes).map(([key, palette]) => (
                    <button
                      key={key}
                      onClick={() => handleColorThemeChange(key)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '1rem',
                        padding: '1rem',
                        backgroundColor: activeColorTheme === key 
                          ? `rgba(${palette.primary.slice(1).match(/.{2}/g).map(hex => parseInt(hex, 16)).join(', ')}, 0.15)`
                          : isDarkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)',
                        border: activeColorTheme === key 
                          ? `2px solid ${palette.primary}`
                          : `2px solid ${theme.border}`,
                        borderRadius: '12px',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                        width: '100%',
                        textAlign: 'left'
                      }}
                      onMouseEnter={(e) => {
                        if (activeColorTheme !== key) {
                          e.currentTarget.style.backgroundColor = `rgba(${palette.primary.slice(1).match(/.{2}/g).map(hex => parseInt(hex, 16)).join(', ')}, 0.08)`;
                          e.currentTarget.style.transform = 'translateY(-2px)';
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (activeColorTheme !== key) {
                          e.currentTarget.style.backgroundColor = isDarkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)';
                          e.currentTarget.style.transform = 'translateY(0)';
                        }
                      }}
                    >
                      <div style={{
                        width: '40px',
                        height: '40px',
                        background: `linear-gradient(135deg, ${palette.primary} 0%, ${palette.secondary} 100%)`,
                        borderRadius: '10px',
                        boxShadow: '0 4px 8px rgba(0, 0, 0, 0.15)',
                        flexShrink: 0
                      }}></div>
                      <div style={{ flex: 1 }}>
                        <div style={{
                          fontSize: '1rem',
                          fontWeight: '600',
                          color: activeColorTheme === key ? palette.primary : theme.text,
                          marginBottom: '0.25rem'
                        }}>
                          {palette.name}
                        </div>
                        <div style={{
                          fontSize: '0.75rem',
                          color: theme.textSecondary
                        }}>
                          {activeColorTheme === key ? 'Currently Active' : 'Click to apply'}
                        </div>
                      </div>
                      {activeColorTheme === key && (
                        <CheckCircle size={20} style={{ color: palette.primary }} />
                      )}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* System Status Tab */}
          {activeTab === 'system' && (
            <div>
              <h2 style={{
                fontSize: '1.5rem',
                fontWeight: '600',
                color: theme.text,
                marginBottom: '1.5rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                <Monitor size={24} style={{ color: currentPalette.primary }} />
                System Status
              </h2>

              {/* Overall Status Card */}
              <div style={{
                padding: '1.5rem',
                backgroundColor: `rgba(${currentPalette.primary.slice(1).match(/.{2}/g).map(hex => parseInt(hex, 16)).join(', ')}, 0.1)`,
                borderRadius: '12px',
                marginBottom: '2rem',
                border: `1px solid ${currentPalette.primary}40`
              }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  marginBottom: '0.5rem'
                }}>
                  <CheckCircle size={24} style={{ color: currentPalette.primary }} />
                  <h3 style={{
                    fontSize: '1.25rem',
                    fontWeight: '600',
                    color: currentPalette.primary,
                    margin: 0
                  }}>
                    All Systems Operational
                  </h3>
                </div>
                <p style={{
                  fontSize: '0.875rem',
                  color: theme.textSecondary,
                  margin: 0
                }}>
                  HMO Analyser is running smoothly with all services online
                </p>
              </div>

              {/* Individual System Status */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                gap: '1rem',
                marginBottom: '2rem'
              }}>
                {Object.entries(systemStatus).slice(0, 3).map(([key, status]) => (
                  <div
                    key={key}
                    style={{
                      padding: '1.25rem',
                      backgroundColor: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)',
                      borderRadius: '12px',
                      border: `1px solid ${theme.border}`
                    }}
                  >
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.75rem',
                      marginBottom: '0.5rem'
                    }}>
                      <div style={{
                        width: '12px',
                        height: '12px',
                        backgroundColor: status.status === 'online' ? currentPalette.primary : '#ef4444',
                        borderRadius: '50%'
                      }}></div>
                      <span style={{
                        fontSize: '1rem',
                        fontWeight: '600',
                        color: theme.text,
                        textTransform: 'capitalize'
                      }}>
                        {key}
                      </span>
                    </div>
                    <p style={{
                      fontSize: '0.875rem',
                      color: theme.textSecondary,
                      margin: 0
                    }}>
                      {status.message}
                    </p>
                  </div>
                ))}
              </div>

              {/* System Information */}
              <div style={{
                padding: '1.5rem',
                backgroundColor: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)',
                borderRadius: '12px'
              }}>
                <h3 style={{
                  fontSize: '1.125rem',
                  fontWeight: '600',
                  color: theme.text,
                  marginBottom: '1rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}>
                  <Database size={20} />
                  System Information
                </h3>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: '1rem'
                }}>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: theme.textSecondary, marginBottom: '0.25rem' }}>
                      Last Backup
                    </div>
                    <div style={{ fontSize: '0.875rem', fontWeight: '500', color: theme.text }}>
                      {systemStatus.lastBackup}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: theme.textSecondary, marginBottom: '0.25rem' }}>
                      Active Theme
                    </div>
                    <div style={{ fontSize: '0.875rem', fontWeight: '500', color: theme.text }}>
                      {currentPalette.name} {isDarkMode ? '(Dark)' : '(Light)'}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: theme.textSecondary, marginBottom: '0.25rem' }}>
                      System Uptime
                    </div>
                    <div style={{ fontSize: '0.875rem', fontWeight: '500', color: theme.text }}>
                      99.9% (30 days)
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Other tabs placeholder */}
          {activeTab !== 'appearance' && activeTab !== 'system' && (
            <div style={{ textAlign: 'center', padding: '3rem' }}>
              <div style={{
                fontSize: '3rem',
                marginBottom: '1rem'
              }}>
                🚧
              </div>
              <h3 style={{
                fontSize: '1.25rem',
                fontWeight: '600',
                color: theme.text,
                marginBottom: '0.5rem'
              }}>
                Coming Soon
              </h3>
              <p style={{
                fontSize: '0.875rem',
                color: theme.textSecondary,
                margin: 0
              }}>
                This section is under development
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;