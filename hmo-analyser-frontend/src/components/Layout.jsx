// Layout.jsx - Updated with Professional Sidebar Navigation (Fixed)
import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../components/AuthContext';
import { LogOut, User, Home, Plus, History, BarChart3, Users, Map, BookOpen, Settings, ChevronLeft, ChevronRight, Moon, Sun, Calculator } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { useDarkMode } from '../contexts/DarkModeContext';

const Layout = ({ children }) => {
  const location = useLocation();
  const { user, logout, isAuthenticated } = useAuth();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  
  // Use contexts for theme and dark mode
  const { activeColorTheme, setColorTheme, currentPalette, colorPalettes } = useTheme();
  const { isDarkMode, toggleDarkMode } = useDarkMode();

  const baseColors = {
    darkSlate: '#2C3E4A',
    lightCream: '#F5F1E8',
    softGray: '#A8A5A0',
  };

  // Theme configuration
  const theme = isDarkMode ? {
    sidebarBg: `linear-gradient(180deg, ${baseColors.darkSlate} 0%, #1e3a47 100%)`,
    mainBg: '#1a2b32',
    cardBg: '#2c3e4a',
    topBarBg: baseColors.darkSlate,
    text: baseColors.lightCream,
    textSecondary: currentPalette.secondary,
    border: 'rgba(180, 180, 180, 0.2)',
    accent: currentPalette.primary,
    accentHover: currentPalette.secondary
  } : {
    sidebarBg: `linear-gradient(180deg, ${currentPalette.primary} 0%, ${currentPalette.secondary} 100%)`,
    mainBg: baseColors.lightCream,
    cardBg: '#ffffff',
    topBarBg: 'white',
    text: baseColors.darkSlate,
    textSecondary: baseColors.softGray,
    border: 'rgba(168, 165, 160, 0.3)',
    accent: currentPalette.accent,
    accentHover: currentPalette.primary
  };

  const navItems = [
    { path: '/', label: 'Dashboard', icon: Home },
    { path: '/analyze', label: 'Add', icon: Plus },
    { path: '/history', label: 'History', icon: History },
    { path: '/cityanalysis', label: 'Analysis', icon: BarChart3 },
    { path: '/dealcalculator', label: 'Deal Calculator', icon: Calculator},
    { path: '/advertisers', label: 'Advertisers', icon: Users },
    { path: '/map', label: 'Map', icon: Map },
    { path: '/contactbook', label: 'Contacts', icon: BookOpen },
  ];

  const isActive = (path) => {
    return location.pathname === path;
  };

  const handleLogout = () => {
    if (window.confirm('Are you sure you want to log out?')) {
      logout();
    }
  };

  const toggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  // Get the current page title
  const getCurrentPageTitle = () => {
    const currentItem = navItems.find(item => item.path === location.pathname);
    if (currentItem) return currentItem.label;
    if (location.pathname === '/settings') return 'Settings';
    if (location.pathname.startsWith('/property/')) return 'Property Details';
    if (location.pathname.startsWith('/advertiser/')) return 'Advertiser Details';
    if (location.pathname.startsWith('/cityanalysis/')) return 'City Analysis';
    if (location.pathname.startsWith('/dealcalculator')) return 'Deal Calculator';
    return 'Dashboard';
  };

  return (
    <div style={{ 
      display: 'flex', 
      minHeight: '100vh', 
      backgroundColor: theme.mainBg,
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      transition: 'background-color 0.3s ease'
    }}>
      {/* Sidebar */}
      <div style={{
        width: sidebarCollapsed ? '80px' : '280px',
        height: '100vh',
        background: theme.sidebarBg,
        borderRight: `1px solid ${theme.border}`,
        display: 'flex',
        flexDirection: 'column',
        transition: 'width 0.3s ease',
        position: 'fixed',
        left: 0,
        top: 0,
        boxShadow: '4px 0 20px rgba(0, 0, 0, 0.15)',
        zIndex: 1000
      }}>
        {/* Logo Section */}
        <div style={{
          padding: sidebarCollapsed ? '1.5rem 1rem' : '2rem 1.5rem',
          borderBottom: `1px solid ${theme.border}`,
          transition: 'padding 0.3s ease'
        }}>
          <Link to="/" style={{
            display: 'flex',
            alignItems: 'center',
            gap: sidebarCollapsed ? '0' : '12px',
            color: theme.text,
            fontSize: sidebarCollapsed ? '1.2rem' : '1.5rem',
            fontWeight: '700',
            letterSpacing: '-0.5px',
            justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
            transition: 'all 0.3s ease',
            textDecoration: 'none'
          }}>
            <div style={{
              width: '40px',
              height: '40px',
              background: `linear-gradient(135deg, ${currentPalette.secondary} 0%, ${baseColors.lightCream} 100%)`,
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '1.2rem',
              boxShadow: `0 4px 12px rgba(0, 0, 0, 0.2)`,
              flexShrink: 0
            }}>
              🏠
            </div>
            {!sidebarCollapsed && <span>HMO Analyser</span>}
          </Link>
        </div>

        {/* Navigation */}
        <nav style={{
          flex: 1,
          padding: '1.5rem 1rem',
          overflowY: 'auto'
        }}>
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '0.5rem'
          }}>
            {navItems.map(({ path, label, icon: Icon }) => (
              <Link
                key={path}
                to={path}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '0.875rem 1rem',
                  color: isActive(path) ? baseColors.darkSlate : 'rgba(255, 255, 255, 0.9)',
                  borderRadius: '12px',
                  fontSize: '0.875rem',
                  fontWeight: '500',
                  background: isActive(path) 
                    ? `linear-gradient(135deg, ${currentPalette.secondary} 0%, ${baseColors.lightCream} 100%)`
                    : 'transparent',
                  boxShadow: isActive(path) 
                    ? '0 4px 12px rgba(0, 0, 0, 0.15)' 
                    : 'none',
                  transition: 'all 0.2s ease',
                  textDecoration: 'none',
                  width: '100%',
                  justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
                  position: 'relative'
                }}
                onMouseEnter={(e) => {
                  if (!isActive(path)) {
                    e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.15)';
                    e.currentTarget.style.transform = 'translateX(4px)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive(path)) {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.transform = 'translateX(0)';
                  }
                }}
                title={sidebarCollapsed ? label : ''}
              >
                <Icon size={20} style={{ flexShrink: 0 }} />
                {!sidebarCollapsed && <span>{label}</span>}
                
                {/* Active indicator */}
                {isActive(path) && (
                  <div style={{
                    position: 'absolute',
                    right: '-1rem',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    width: '4px',
                    height: '20px',
                    background: `linear-gradient(135deg, ${currentPalette.accent} 0%, ${currentPalette.primary} 100%)`,
                    borderRadius: '2px'
                  }} />
                )}
              </Link>
            ))}
          </div>
        </nav>

        {/* Settings & Controls Section */}
        <div style={{
          padding: '1rem',
          borderTop: `1px solid ${theme.border}`,
          marginTop: 'auto'
        }}>
          {/* Settings Link */}
          <Link
            to="/settings"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '0.875rem 1rem',
              color: isActive('/settings') ? baseColors.darkSlate : 'rgba(255, 255, 255, 0.8)',
              borderRadius: '12px',
              fontSize: '0.875rem',
              fontWeight: '500',
              background: isActive('/settings') 
                ? `linear-gradient(135deg, ${currentPalette.secondary} 0%, ${baseColors.lightCream} 100%)`
                : 'transparent',
              textDecoration: 'none',
              width: '100%',
              justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
              marginBottom: '0.5rem',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => {
              if (!isActive('/settings')) {
                e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
              }
            }}
            onMouseLeave={(e) => {
              if (!isActive('/settings')) {
                e.currentTarget.style.backgroundColor = 'transparent';
              }
            }}
            title={sidebarCollapsed ? 'Settings' : ''}
          >
            <Settings size={20} style={{ flexShrink: 0 }} />
            {!sidebarCollapsed && <span>Settings</span>}
          </Link>

          {/* Dark Mode Toggle */}
          <button
            onClick={toggleDarkMode}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '0.875rem 1rem',
              color: 'rgba(255, 255, 255, 0.8)',
              border: 'none',
              borderRadius: '12px',
              fontSize: '0.875rem',
              fontWeight: '500',
              background: 'transparent',
              cursor: 'pointer',
              width: '100%',
              textAlign: 'left',
              justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
              marginBottom: '1rem',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
            }}
            title={sidebarCollapsed ? (isDarkMode ? 'Light Mode' : 'Dark Mode') : ''}
          >
            {isDarkMode ? <Sun size={20} /> : <Moon size={20} />}
            {!sidebarCollapsed && <span>{isDarkMode ? 'Light Mode' : 'Dark Mode'}</span>}
          </button>

          {/* User Info - Only show when authenticated */}
          {isAuthenticated && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: sidebarCollapsed ? '0' : '12px',
              padding: '1rem',
              backgroundColor: 'rgba(255, 255, 255, 0.15)',
              borderRadius: '12px',
              fontSize: '0.875rem',
              color: theme.text,
              marginBottom: '0.5rem',
              justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
              transition: 'all 0.3s ease'
            }}>
              <div style={{
                width: '36px',
                height: '36px',
                background: `linear-gradient(135deg, ${currentPalette.accent} 0%, ${currentPalette.primary} 100%)`,
                borderRadius: '10px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.2)'
              }}>
                <User size={18} color="white" />
              </div>
              {!sidebarCollapsed && (
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontWeight: '600', fontSize: '0.875rem' }}>
                    {user?.full_name || user?.username || 'User'}
                  </div>
                  <div style={{ fontSize: '0.75rem', opacity: 0.7 }}>
                    Administrator
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Logout Button - Only show when authenticated */}
          {isAuthenticated && (
            <button
              onClick={handleLogout}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '0.875rem 1rem',
                backgroundColor: `rgba(${currentPalette.primary.slice(1).match(/.{2}/g).map(hex => parseInt(hex, 16)).join(', ')}, 0.2)`,
                color: currentPalette.secondary,
                border: `1px solid rgba(${currentPalette.primary.slice(1).match(/.{2}/g).map(hex => parseInt(hex, 16)).join(', ')}, 0.3)`,
                borderRadius: '12px',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: '500',
                transition: 'all 0.2s ease',
                width: '100%',
                justifyContent: sidebarCollapsed ? 'center' : 'flex-start'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = `rgba(${currentPalette.primary.slice(1).match(/.{2}/g).map(hex => parseInt(hex, 16)).join(', ')}, 0.3)`;
                e.currentTarget.style.color = '#ffffff';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = `rgba(${currentPalette.primary.slice(1).match(/.{2}/g).map(hex => parseInt(hex, 16)).join(', ')}, 0.2)`;
                e.currentTarget.style.color = currentPalette.secondary;
              }}
              title={sidebarCollapsed ? 'Logout' : ''}
            >
              <LogOut size={18} style={{ flexShrink: 0 }} />
              {!sidebarCollapsed && <span>Logout</span>}
            </button>
          )}
        </div>

        {/* Collapse Toggle */}
        <button
          onClick={toggleSidebar}
          style={{
            position: 'absolute',
            right: '-12px',
            top: '50%',
            transform: 'translateY(-50%)',
            width: '24px',
            height: '24px',
            backgroundColor: theme.cardBg,
            border: `1px solid ${theme.border}`,
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
            transition: 'all 0.2s ease',
            zIndex: 10,
            color: theme.text
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-50%) scale(1.1)';
            e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.2)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(-50%) scale(1)';
            e.currentTarget.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.15)';
          }}
        >
          {sidebarCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
        </button>
      </div>

      {/* Main Content */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100vh',
        marginLeft: sidebarCollapsed ? '80px' : '280px',
        transition: 'margin-left 0.3s ease'
      }}>
        {/* Top Bar */}
        <header style={{
          backgroundColor: theme.topBarBg,
          borderBottom: `1px solid ${theme.border}`,
          padding: '1rem 2rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
          position: 'sticky',
          top: 0,
          zIndex: 100,
          transition: 'background-color 0.3s ease'
        }}>
          <div>
            <h1 style={{
              fontSize: '1.5rem',
              fontWeight: '700',
              color: theme.text,
              margin: 0
            }}>
              {getCurrentPageTitle()}
            </h1>
            <p style={{
              fontSize: '0.875rem',
              color: theme.textSecondary,
              margin: '0.25rem 0 0 0'
            }}>
              Welcome back, manage your HMO properties with ease
            </p>
          </div>
        </header>

        {/* Main Content Area */}
        <main style={{
          flex: 1,
          padding: '2rem',
          overflow: 'auto',
          backgroundColor: theme.mainBg
        }}>
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;