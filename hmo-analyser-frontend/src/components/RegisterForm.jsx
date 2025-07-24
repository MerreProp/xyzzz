// Create new file: components/RegisterForm.jsx

import React, { useState } from 'react';
import { Mail, Lock, User, UserCheck, Loader2, Eye, EyeOff } from 'lucide-react';
import { useAuth } from './AuthContext';

const RegisterForm = ({ onSwitchToLogin, onSuccess }) => {
  const { register } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    full_name: '',
    password: '',
    confirmPassword: ''
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }
    
    if (!formData.username.trim()) {
      newErrors.username = 'Username is required';
    } else if (formData.username.length < 3) {
      newErrors.username = 'Username must be at least 3 characters';
    } else if (!/^[a-zA-Z0-9_]+$/.test(formData.username)) {
      newErrors.username = 'Username can only contain letters, numbers, and underscores';
    }
    
    if (!formData.full_name.trim()) {
      newErrors.full_name = 'Full name is required';
    }
    
    if (!formData.password.trim()) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }
    
    if (!formData.confirmPassword.trim()) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
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
      const { confirmPassword, ...registerData } = formData;
      const result = await register(registerData);
      
      if (result.success) {
        onSuccess();
      } else {
        setErrors({ general: result.error });
      }
    } catch (error) {
      setErrors({ general: 'Registration failed. Please try again.' });
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
          Create Account
        </h2>
        <p style={{ color: '#6b7280' }}>
          Join us to start managing your contacts
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

          {/* Username */}
          <div>
            <label style={{
              display: 'block',
              fontSize: '14px',
              fontWeight: '500',
              color: '#111827',
              marginBottom: '6px'
            }}>
              Username
            </label>
            <div style={{ position: 'relative' }}>
              <User style={{
                position: 'absolute',
                left: '12px',
                top: '50%',
                transform: 'translateY(-50%)',
                color: '#9ca3af',
                width: '20px',
                height: '20px'
              }} />
              <input
                type="text"
                value={formData.username}
                onChange={(e) => handleChange('username', e.target.value)}
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '12px 12px 12px 44px',
                  border: `1px solid ${errors.username ? '#f87171' : '#d1d5db'}`,
                  borderRadius: '6px',
                  fontSize: '14px',
                  backgroundColor: loading ? '#f9fafb' : 'white'
                }}
                placeholder="Choose a username"
              />
            </div>
            {errors.username && (
              <p style={{ color: '#dc2626', fontSize: '12px', margin: '4px 0 0' }}>
                {errors.username}
              </p>
            )}
          </div>

          {/* Full Name */}
          <div>
            <label style={{
              display: 'block',
              fontSize: '14px',
              fontWeight: '500',
              color: '#111827',
              marginBottom: '6px'
            }}>
              Full Name
            </label>
            <div style={{ position: 'relative' }}>
              <UserCheck style={{
                position: 'absolute',
                left: '12px',
                top: '50%',
                transform: 'translateY(-50%)',
                color: '#9ca3af',
                width: '20px',
                height: '20px'
              }} />
              <input
                type="text"
                value={formData.full_name}
                onChange={(e) => handleChange('full_name', e.target.value)}
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '12px 12px 12px 44px',
                  border: `1px solid ${errors.full_name ? '#f87171' : '#d1d5db'}`,
                  borderRadius: '6px',
                  fontSize: '14px',
                  backgroundColor: loading ? '#f9fafb' : 'white'
                }}
                placeholder="Enter your full name"
              />
            </div>
            {errors.full_name && (
              <p style={{ color: '#dc2626', fontSize: '12px', margin: '4px 0 0' }}>
                {errors.full_name}
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
                placeholder="Choose a password"
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

          {/* Confirm Password */}
          <div>
            <label style={{
              display: 'block',
              fontSize: '14px',
              fontWeight: '500',
              color: '#111827',
              marginBottom: '6px'
            }}>
              Confirm Password
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
                type={showConfirmPassword ? 'text' : 'password'}
                value={formData.confirmPassword}
                onChange={(e) => handleChange('confirmPassword', e.target.value)}
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '12px 44px 12px 44px',
                  border: `1px solid ${errors.confirmPassword ? '#f87171' : '#d1d5db'}`,
                  borderRadius: '6px',
                  fontSize: '14px',
                  backgroundColor: loading ? '#f9fafb' : 'white'
                }}
                placeholder="Confirm your password"
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
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
                {showConfirmPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
            {errors.confirmPassword && (
              <p style={{ color: '#dc2626', fontSize: '12px', margin: '4px 0 0' }}>
                {errors.confirmPassword}
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
              Creating Account...
            </>
          ) : (
            'Create Account'
          )}
        </button>
      </form>

      {/* Switch to Login */}
      <div style={{ textAlign: 'center', marginTop: '24px' }}>
        <p style={{ color: '#6b7280', fontSize: '14px' }}>
          Already have an account?{' '}
          <button
            onClick={onSwitchToLogin}
            style={{
              color: '#2563eb',
              textDecoration: 'underline',
              border: 'none',
              backgroundColor: 'transparent',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Sign in here
          </button>
        </p>
      </div>
    </div>
  );
};

export default RegisterForm;