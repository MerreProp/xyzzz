// Create new file: components/UserMenu.jsx

import React, { useState, useRef, useEffect } from 'react';
import { User, LogOut, Settings, ChevronDown } from 'lucide-react';
import { useAuth } from './AuthContext';

const UserMenu = () => {
  const { user, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef(null);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleLogout = () => {
    logout();
    setIsOpen(false);
  };

  return (
    <div style={{ position: 'relative' }} ref={menuRef}>
      {/* Menu Trigger */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '8px 12px',
          border: '1px solid #d1d5db',
          borderRadius: '6px',
          backgroundColor: 'white',
          color: '#374151',
          cursor: 'pointer',
          fontSize: '14px'
        }}
      >
        <User style={{ width: '16px', height: '16px' }} />
        <span>{user?.full_name || user?.username}</span>
        <ChevronDown style={{ width: '16px', height: '16px' }} />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div style={{
          position: 'absolute',
          top: '100%',
          right: 0,
          marginTop: '4px',
          backgroundColor: 'white',
          border: '1px solid #d1d5db',
          borderRadius: '6px',
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
          minWidth: '200px',
          zIndex: 50
        }}>
          {/* User Info */}
          <div style={{
            padding: '12px 16px',
            borderBottom: '1px solid #e5e7eb'
          }}>
            <p style={{
              fontSize: '14px',
              fontWeight: '500',
              color: '#111827',
              margin: 0
            }}>
              {user?.full_name}
            </p>
            <p style={{
              fontSize: '12px',
              color: '#6b7280',
              margin: 0
            }}>
              {user?.email}
            </p>
          </div>

          {/* Menu Items */}
          <div style={{ padding: '8px 0' }}>
            <button
              onClick={() => {
                setIsOpen(false);
                // Add settings functionality later
              }}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 16px',
                border: 'none',
                backgroundColor: 'transparent',
                color: '#374151',
                cursor: 'pointer',
                fontSize: '14px',
                textAlign: 'left'
              }}
            >
              <Settings style={{ width: '16px', height: '16px' }} />
              Settings
            </button>

            <button
              onClick={handleLogout}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 16px',
                border: 'none',
                backgroundColor: 'transparent',
                color: '#dc2626',
                cursor: 'pointer',
                fontSize: '14px',
                textAlign: 'left'
              }}
            >
              <LogOut style={{ width: '16px', height: '16px' }} />
              Sign Out
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserMenu;