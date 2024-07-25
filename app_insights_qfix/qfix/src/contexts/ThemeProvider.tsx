import React, { createContext, useState, useContext, ReactNode } from 'react';
import { createTheme, ThemeProvider as FluentThemeProvider, Theme } from '@fluentui/react';

type ThemeContextType = {
  isDarkTheme: boolean;
  toggleTheme: () => void;
  getTheme: () => Theme
  getInverseTheme: () => Theme;
};

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const lightTheme = createTheme({
  palette: {
    themePrimary: '#0078d4',
    themeLighterAlt: '#f3f9fd',
    themeLighter: '#d0e7f8',
    themeLight: '#a9d3f2',
    themeTertiary: '#5ca9e5',
    themeSecondary: '#1a86d9',
    themeDarkAlt: '#006cbe',
    themeDark: '#005ba1',
    themeDarker: '#004377',
    neutralLighterAlt: '#f8f8f8',
    neutralLighter: '#f4f4f4',
    neutralLight: '#eaeaea',
    neutralQuaternaryAlt: '#dadada',
    neutralQuaternary: '#d0d0d0',
    neutralTertiaryAlt: '#c8c8c8',
    neutralTertiary: '#c2c2c2',
    neutralSecondary: '#858585',
    neutralPrimaryAlt: '#4b4b4b',
    neutralPrimary: '#333333',
    neutralDark: '#272727',
    black: '#1d1d1d',
    white: '#ffffff',
  },
});

const darkTheme = createTheme({
  palette: {
    themePrimary: '#0078d4',
    themeLighterAlt: '#f3f9fd',
    themeLighter: '#d0e7f8',
    themeLight: '#a9d3f2',
    themeTertiary: '#5ca9e5',
    themeSecondary: '#1a86d9',
    themeDarkAlt: '#006cbe',
    themeDark: '#005ba1',
    themeDarker: '#004377',
    neutralLighterAlt: '#2f2f2f',
    neutralLighter: '#2c2c2c',
    neutralLight: '#282828',
    neutralQuaternaryAlt: '#252525',
    neutralQuaternary: '#232323',
    neutralTertiaryAlt: '#202020',
    neutralTertiary: '#c8c8c8',
    neutralSecondary: '#d0d0d0',
    neutralPrimaryAlt: '#dadada',
    neutralPrimary: '#ffffff',
    neutralDark: '#f4f4f4',
    black: '#f8f8f8',
    white: '#1b1b1b',
  },
});

export const ThemeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isDarkTheme, setIsDarkTheme] = useState(false);

  const toggleTheme = () => {
    setIsDarkTheme(!isDarkTheme);
  };
  const getTheme = () => {
    return isDarkTheme ? darkTheme : lightTheme
  };
  const getInverseTheme = () => {
    return !isDarkTheme ? darkTheme : lightTheme
  };

  return (
    <ThemeContext.Provider value={{ isDarkTheme, toggleTheme, getTheme, getInverseTheme }}>
      <FluentThemeProvider theme={isDarkTheme ? darkTheme : lightTheme}>
        {children}
      </FluentThemeProvider>
    </ThemeContext.Provider>
  );
};

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
