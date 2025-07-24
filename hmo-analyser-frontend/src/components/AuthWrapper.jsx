// Create new file: components/AuthWrapper.jsx

import React from 'react';
import { useAuth } from './AuthContext';
import { Loader2 } from 'lucide-react';
import LoginPage from './LoginPage';

const AuthWrapper = ({ children }) => {
  const { user, loading, isAuthenticated } = useAuth();

  if (loading) {
    return (
      <div style={{
        minHeight: '100vh',
        backgroundColor: '#f9fafb',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <div style={{ textAlign: 'center' }}>
          <Loader2 style={{
            width: '48px',
            height: '48px',
            color: '#2563eb',
            margin: '0 auto 16px',
            animation: 'spin 1s linear infinite'
          }} />
          <h3 style={{
            fontSize: '18px',
            fontWeight: '500',
            color: '#111827',
            marginBottom: '8px'
          }}>
            Loading...
          </h3>
          <p style={{ color: '#6b7280' }}>
            Please wait while we authenticate you.
          </p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return children;
};

export default AuthWrapper;
