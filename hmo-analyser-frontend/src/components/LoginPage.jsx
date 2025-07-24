// Create new file: components/LoginPage.jsx

import React, { useState } from 'react';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';

const LoginPage = () => {
  const [isLogin, setIsLogin] = useState(true);

  const handleSuccess = () => {
    // The AuthContext will handle the state update
    // The user will be redirected automatically
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#f9fafb',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '400px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center'
      }}>
        {/* Logo/Header */}
        <div style={{
          textAlign: 'center',
          marginBottom: '32px'
        }}>
          <h1 style={{
            fontSize: '32px',
            fontWeight: 'bold',
            color: '#111827',
            marginBottom: '8px'
          }}>
            📞 Contact Book
          </h1>
          <p style={{
            color: '#6b7280',
            fontSize: '16px'
          }}>
            Manage your property contacts and relationships
          </p>
        </div>

        {/* Auth Forms */}
        {isLogin ? (
          <LoginForm
            onSwitchToRegister={() => setIsLogin(false)}
            onSuccess={handleSuccess}
          />
        ) : (
          <RegisterForm
            onSwitchToLogin={() => setIsLogin(true)}
            onSuccess={handleSuccess}
          />
        )}
      </div>
    </div>
  );
};

export default LoginPage;