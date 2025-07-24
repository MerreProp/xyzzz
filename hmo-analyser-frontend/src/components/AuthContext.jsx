// Create new file: components/AuthContext.jsx

import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('access_token'));
  const [loading, setLoading] = useState(true);

  // API base URL
  const API_BASE = process.env.NODE_ENV === 'production' 
    ? '/api' 
    : 'http://localhost:8000/api';

  // API request helper with auth
    const apiRequest = async (url, method = 'GET', body = null) => {
    const config = {
        method,
        headers: {
        'Content-Type': 'application/json',
        },
    };

    if (body) {
        config.body = JSON.stringify(body);
    }

    if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}${url}`, config);
    
    if (response.status === 401) {
        // Token expired or invalid
        logout();
        throw new Error('Not authenticated');
    }
    
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }
    
    return response.json();
    };

  // Load user data on mount
  useEffect(() => {
    const loadUser = async () => {
      if (token) {
        try {
          const userData = await apiRequest('/auth/me');
          setUser(userData);
        } catch (error) {
          console.error('Failed to load user:', error);
          localStorage.removeItem('access_token');
          setToken(null);
        }
      }
      setLoading(false);
    };

    loadUser();
  }, [token]);

    const login = async (email, password) => {
    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
        });

        if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Login failed');
        }

        const data = await response.json();
        const accessToken = data.access_token;

        localStorage.setItem('access_token', accessToken);
        setToken(accessToken);

        // Load user data using the NEW token directly (not from state)
        const userData = await fetch(`${API_BASE}/auth/me`, {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}` // Use the new token directly
        }
        });

        if (!userData.ok) {
        throw new Error('Failed to fetch user data');
        }

        const userInfo = await userData.json();
        setUser(userInfo);

        return { success: true };
    } catch (error) {
        console.error('Login error:', error);
        return { success: false, error: error.message };
    }
    };

  const register = async (userData) => {
    try {
      const response = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Registration failed');
      }

      const newUser = await response.json();
      
      // Auto-login after registration
      const loginResult = await login(userData.email, userData.password);
      return loginResult;
    } catch (error) {
      console.error('Registration error:', error);
      return { success: false, error: error.message };
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setToken(null);
    setUser(null);
  };

  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    apiRequest,
    isAuthenticated: !!user,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};