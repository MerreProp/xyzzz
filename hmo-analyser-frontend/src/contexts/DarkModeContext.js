import React, { createContext, useContext, useState, useEffect } from 'react';

const DarkModeContext = createContext();

export const useDarkMode = () => {
  const context = useContext(DarkModeContext);
  if (!context) {
    throw new Error('useDarkMode must be used within a DarkModeProvider');
  }
  return context;
};

export const DarkModeProvider = ({ children }) => {
  // Check localStorage for saved preference, default to light mode
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    return saved ? JSON.parse(saved) : false;
  });

  // Update localStorage and document class when dark mode changes
  useEffect(() => {
    localStorage.setItem('darkMode', JSON.stringify(isDarkMode));
    
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
      document.body.style.backgroundColor = '#1f2937';
      document.body.style.color = '#f9fafb';
    } else {
      document.documentElement.classList.remove('dark');
      document.body.style.backgroundColor = '#ffffff';
      document.body.style.color = '#1f2937';
    }
  }, [isDarkMode]);

  const toggleDarkMode = () => {
    setIsDarkMode(prev => !prev);
  };

  // Theme object with all the colors you'll need
  const theme = {
    isDarkMode,
    colors: {
      // Background colors
      background: isDarkMode ? '#1f2937' : '#ffffff',
      backgroundSecondary: isDarkMode ? '#374151' : '#f9fafb',
      backgroundTertiary: isDarkMode ? '#4b5563' : '#f3f4f6',
      
      // Text colors
      text: isDarkMode ? '#f9fafb' : '#1f2937',
      textSecondary: isDarkMode ? '#d1d5db' : '#6b7280',
      textMuted: isDarkMode ? '#9ca3af' : '#6b7280',
      
      // Border colors
      border: isDarkMode ? '#4b5563' : '#e5e7eb',
      borderLight: isDarkMode ? '#374151' : '#f3f4f6',
      
      // Card colors
      card: isDarkMode ? '#374151' : '#ffffff',
      cardHover: isDarkMode ? '#4b5563' : '#f9fafb',
      
      // Button colors
      primary: '#3b82f6',
      primaryHover: '#2563eb',
      secondary: isDarkMode ? '#6b7280' : '#6b7280',
      secondaryHover: isDarkMode ? '#4b5563' : '#9ca3af',
      
      // Status colors (these stay the same in both modes)
      success: '#10b981',
      warning: '#f59e0b',
      error: '#ef4444',
      info: '#3b82f6',
      
      // Success/Error backgrounds
      successBg: isDarkMode ? '#064e3b' : '#dcfce7',
      warningBg: isDarkMode ? '#78350f' : '#fef3c7',
      errorBg: isDarkMode ? '#7f1d1d' : '#fee2e2',
      infoBg: isDarkMode ? '#1e3a8a' : '#dbeafe',
    }
  };

  return (
    <DarkModeContext.Provider value={{ isDarkMode, toggleDarkMode, theme }}>
      {children}
    </DarkModeContext.Provider>
  );
};