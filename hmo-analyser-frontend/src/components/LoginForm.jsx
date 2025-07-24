// Create new file: components/LoginForm.jsx

import React, { useState } from 'react';
import { Mail, Lock, Loader2, Eye, EyeOff } from 'lucide-react';
import { useAuth } from './AuthContext';

const LoginForm = ({ onSwitchToRegister, onSuccess }) => {
  const { login } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }
    
    if (!formData.password.trim()) {
      newErrors.password = 'Password is required';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setLoading(true);
    try {
      const result = await login(formData.email, formData.password);
      
      if (result.success) {
        onSuccess();
      } else {
        setErrors({ general: result.error });
      }
    } catch (error) {
      setErrors({ general: 'Login failed. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
    if (errors.general) {
      setErrors(prev => ({ ...prev, general: undefined }));
    }
  };

  return (
    <div style={{
      backgroundColor: 'white',
      borderRadius: '8px',
      padding: '32px',
      width: '100%',
      maxWidth: '400px',
      boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)'
    }}>
      <div style={{ textAlign: 'center', marginBottom: '32px' }}>
        <h2 style={{ fontSize: '28px', fontWeight: 'bold', color: '#111827', marginBottom: '8px' }}>
          Welcome Back
        </h2>
        <p style={{ color: '#6b7280' }}>
          Sign in to access your contact book
        </p>
      </div>

      {errors.general && (
        <div style={{
          backgroundColor: '#fef2f2',
          border: '1px solid #fecaca',
          borderRadius: '6px',
          padding: '12px',
          marginBottom: '24px'
        }}>
          <p style={{ color: '#dc2626', margin: 0, fontSize: '14px' }}>
            {errors.general}
          </p>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Email */}
          <div>
            <label style={{
              display: 'block',
              fontSize: '14px',
              fontWeight: '500',
              color: '#111827',
              marginBottom: '6px'
            }}>
              Email Address
            </label>
            <div style={{ position: 'relative' }}>
              <Mail style={{
                position: 'absolute',
                left: '12px',
                top: '50%',
                transform: 'translateY(-50%)',
                color: '#9ca3af',
                width: '20px',
                height: '20px'
              }} />
              <input
                type="email"
                value={formData.email}
                onChange={(e) => handleChange('email', e.target.value)}
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '12px 12px 12px 44px',
                  border: `1px solid ${errors.email ? '#f87171' : '#d1d5db'}`,
                  borderRadius: '6px',
                  fontSize: '14px',
                  backgroundColor: loading ? '#f9fafb' : 'white'
                }}
                placeholder="Enter your email"
              />
            </div>
            {errors.email && (
              <p style={{ color: '#dc2626', fontSize: '12px', margin: '4px 0 0' }}>
                {errors.email}
              </p>
            )}
          </div>

          {/* Password */}
          <div>
            <label style={{
              display: 'block',
              fontSize: '14px',
              fontWeight: '500',
              color: '#111827',
              marginBottom: '6px'
            }}>
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <Lock style={{
                position: 'absolute',
                left: '12px',
                top: '50%',
                transform: 'translateY(-50%)',
                color: '#9ca3af',
                width: '20px',
                height: '20px'
              }} />
              <input
                type={showPassword ? 'text' : 'password'}
                value={formData.password}
                onChange={(e) => handleChange('password', e.target.value)}
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '12px 44px 12px 44px',
                  border: `1px solid ${errors.password ? '#f87171' : '#d1d5db'}`,
                  borderRadius: '6px',
                  fontSize: '14px',
                  backgroundColor: loading ? '#f9fafb' : 'white'
                }}
                placeholder="Enter your password"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '12px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  border: 'none',
                  backgroundColor: 'transparent',
                  color: '#9ca3af',
                  cursor: 'pointer',
                  padding: '4px'
                }}
              >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
            {errors.password && (
              <p style={{ color: '#dc2626', fontSize: '12px', margin: '4px 0 0' }}>
                {errors.password}
              </p>
            )}
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '12px',
            fontSize: '16px',
            fontWeight: '500',
            borderRadius: '6px',
            border: '1px solid transparent',
            backgroundColor: '#2563eb',
            color: 'white',
            cursor: loading ? 'not-allowed' : 'pointer',
            marginTop: '24px'
          }}
        >
          {loading ? (
            <>
              <Loader2 style={{ width: '20px', height: '20px', marginRight: '8px', animation: 'spin 1s linear infinite' }} />
              Signing In...
            </>
          ) : (
            'Sign In'
          )}
        </button>
      </form>

      {/* Switch to Register */}
      <div style={{ textAlign: 'center', marginTop: '24px' }}>
        <p style={{ color: '#6b7280', fontSize: '14px' }}>
          Don't have an account?{' '}
          <button
            onClick={onSwitchToRegister}
            style={{
              color: '#2563eb',
              textDecoration: 'underline',
              border: 'none',
              backgroundColor: 'transparent',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Create one here
          </button>
        </p>
      </div>
    </div>
  );
};

export default LoginForm;