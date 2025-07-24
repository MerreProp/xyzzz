// Layout.jsx - Complete file with logout functionality

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../components/AuthContext';
import { LogOut, User } from 'lucide-react';

const Layout = ({ children }) => {
  const location = useLocation();
  const { user, logout, isAuthenticated } = useAuth();

  const isActive = (path) => {
    return location.pathname === path;
  };

  const handleLogout = () => {
    if (window.confirm('Are you sure you want to log out?')) {
      logout();
    }
  };

  return (
    <div className="layout">
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <Link 
              to="/" 
              className={`nav-link ${isActive('/') ? 'active' : ''}`}
            >
              🏠 HMO Property Analyser
            </Link>
          </div>
          
          <nav className="nav">
            <Link 
              to="/analyze" 
              className={`nav-link ${isActive('/analyze') ? 'active' : ''}`}
            >
              Add
            </Link>
            <Link 
              to="/history" 
              className={`nav-link ${isActive('/history') ? 'active' : ''}`}
            >
              History
            </Link>
            <Link 
              to="/cityanalysis" 
              className={`nav-link ${isActive('/cityanalysis') ? 'active' : ''}`}
            >
              Analysis
            </Link>
            <Link 
              to="/advertisers" 
              className={`nav-link ${isActive('/advertisers') ? 'active' : ''}`}
            >
              Advertisers
            </Link>
            <Link 
              to="/map" 
              className={`nav-link ${isActive('/map') ? 'active' : ''}`}
            >
              Map
            </Link>
            <Link 
              to="/contactbook" 
              className={`nav-link ${isActive('/contactbook') ? 'active' : ''}`}
            >
              Contacts
            </Link>
          </nav>

          {/* User Section - Only show when authenticated */}
          {isAuthenticated && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '1rem',
              marginLeft: 'auto'
            }}>
              {/* User Info */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.5rem 1rem',
                backgroundColor: '#f3f4f6',
                borderRadius: '6px',
                fontSize: '0.875rem',
                color: '#374151'
              }}>
                <User size={16} />
                <span style={{ fontWeight: '500' }}>
                  {user?.full_name || user?.username || 'User'}
                </span>
              </div>

              {/* Logout Button */}
              <button
                onClick={handleLogout}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.5rem 1rem',
                  backgroundColor: '#dc2626',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '0.875rem',
                  fontWeight: '500',
                  transition: 'background-color 0.2s'
                }}
                onMouseOver={(e) => e.target.style.backgroundColor = '#b91c1c'}
                onMouseOut={(e) => e.target.style.backgroundColor = '#dc2626'}
                title="Log out"
              >
                <LogOut size={16} />
                Logout
              </button>
            </div>
          )}
        </div>
      </header>
      <main className="main-content">
        {children}
      </main>
    </div>
  );
};

export default Layout;