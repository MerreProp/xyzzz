// src/contexts/ThemeContext.jsx
import React, { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext();

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

export const ThemeProvider = ({ children }) => {
  // Initialize with saved theme or default to terracotta
  const [activeColorTheme, setActiveColorTheme] = useState(() => {
    const saved = localStorage.getItem('hmo-color-theme');
    return saved || 'terracotta';
  });

  // Extended earthy color palette
  const colorPalettes = {
    terracotta: {
      primary: '#C17A6B',
      secondary: '#D49477',
      accent: '#7A94A8',
      name: 'Terracotta'
    },
    dustyBlue: {
      primary: '#7A94A8',
      secondary: '#9BB4C7',
      accent: '#C17A6B',
      name: 'Dusty Blue'
    },
    warmBeige: {
      primary: '#D4C4A8',
      secondary: '#E6D7C3',
      accent: '#9BAA8C',
      name: 'Warm Beige'
    },
    sageGreen: {
      primary: '#9BAA8C',
      secondary: '#B5C4A7',
      accent: '#C17A6B',
      name: 'Sage Green'
    },
    sunflower: {
      primary: '#E6B85C',
      secondary: '#F2CC7A',
      accent: '#7A94A8',
      name: 'Sunflower'
    },
    skyBlue: {
      primary: '#A8C5D1',
      secondary: '#BFD4DF',
      accent: '#E6B85C',
      name: 'Sky Blue'
    },
    mintGreen: {
      primary: '#B8D4C2',
      secondary: '#CDE2D4',
      accent: '#E6B85C',
      name: 'Mint Green'
    },
    salmonPink: {
      primary: '#E6A190',
      secondary: '#F0B5A8',
      accent: '#A8C5D1',
      name: 'Salmon Pink'
    }
  };

  // Save theme to localStorage whenever it changes
  const setColorTheme = (themeKey) => {
    setActiveColorTheme(themeKey);
    localStorage.setItem('hmo-color-theme', themeKey);
  };

  // Get current palette
  const currentPalette = colorPalettes[activeColorTheme];

  return (
    <ThemeContext.Provider value={{
      activeColorTheme,
      setColorTheme,
      colorPalettes,
      currentPalette
    }}>
      {children}
    </ThemeContext.Provider>
  );
};