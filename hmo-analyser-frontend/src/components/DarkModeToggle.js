import React from 'react';
import { useDarkMode } from '../contexts/DarkModeContext';

const DarkModeToggle = ({ 
  size = 'medium', 
  position = 'relative',
  showText = true,
  style = {} 
}) => {
  const { isDarkMode, toggleDarkMode, theme } = useDarkMode();

  const sizes = {
    small: {
      button: { width: '40px', height: '40px', fontSize: '1rem' },
      text: { fontSize: '0.75rem' }
    },
    medium: {
      button: { width: '48px', height: '48px', fontSize: '1.25rem' },
      text: { fontSize: '0.875rem' }
    },
    large: {
      button: { width: '56px', height: '56px', fontSize: '1.5rem' },
      text: { fontSize: '1rem' }
    }
  };

  const positions = {
    'fixed-top-right': {
      position: 'fixed',
      top: '1rem',
      right: '1rem',
      zIndex: 1000
    },
    'fixed-bottom-right': {
      position: 'fixed',
      bottom: '1rem',
      right: '1rem',
      zIndex: 1000
    },
    'relative': {
      position: 'relative'
    }
  };

  const currentSize = sizes[size];
  const currentPosition = positions[position];

  return (
    <div style={{ 
      display: 'flex', 
      alignItems: 'center', 
      gap: '0.5rem',
      ...currentPosition,
      ...style 
    }}>
      <button
        onClick={toggleDarkMode}
        style={{
          backgroundColor: theme.colors.card,
          border: `2px solid ${theme.colors.border}`,
          borderRadius: '50%',
          cursor: 'pointer',
          transition: 'all 0.3s ease',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: isDarkMode 
            ? '0 4px 6px rgba(0, 0, 0, 0.3)' 
            : '0 4px 6px rgba(0, 0, 0, 0.1)',
          color: theme.colors.text,
          ...currentSize.button
        }}
        onMouseEnter={(e) => {
          e.target.style.backgroundColor = theme.colors.cardHover;
          e.target.style.transform = 'scale(1.05)';
        }}
        onMouseLeave={(e) => {
          e.target.style.backgroundColor = theme.colors.card;
          e.target.style.transform = 'scale(1)';
        }}
        title={isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
      >
        {isDarkMode ? '☀️' : '🌙'}
      </button>
      
      {showText && (
        <span style={{ 
          color: theme.colors.textSecondary,
          fontWeight: '500',
          ...currentSize.text
        }}>
          {isDarkMode ? 'Light Mode' : 'Dark Mode'}
        </span>
      )}
    </div>
  );
};

export default DarkModeToggle;