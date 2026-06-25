import { createContext, useEffect, useState } from 'react';

export type ColorScheme = 'light' | 'dark';

interface ThemeContextType {
  colorScheme: ColorScheme;
  toggleColorScheme: () => void;
  setColorScheme: (scheme: ColorScheme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

// Export the context for use in hooks
export { ThemeContext };

interface ThemeProviderProps {
  children: React.ReactNode;
}

const STORAGE_KEY = 'chat-app-color-scheme';

const getInitialColorScheme = (): ColorScheme => {
  // First, check localStorage
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === 'light' || stored === 'dark') {
    return stored;
  }

  // If not in localStorage, detect browser preference
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark';
  }

  // Default to light
  return 'light';
};

export const ThemeProvider = ({ children }: ThemeProviderProps) => {
  const [colorScheme, setColorSchemeState] = useState<ColorScheme>(getInitialColorScheme);

  const setColorScheme = (scheme: ColorScheme) => {
    setColorSchemeState(scheme);
    localStorage.setItem(STORAGE_KEY, scheme);
  };

  const toggleColorScheme = () => {
    setColorScheme(colorScheme === 'light' ? 'dark' : 'light');
  };

  // Listen for browser theme changes
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleChange = (e: MediaQueryListEvent) => {
      // Only auto-update if user hasn't manually set a preference
      const storedScheme = localStorage.getItem(STORAGE_KEY);
      if (!storedScheme) {
        setColorSchemeState(e.matches ? 'dark' : 'light');
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return (
    <ThemeContext.Provider value={{ colorScheme, toggleColorScheme, setColorScheme }}>
      {children}
    </ThemeContext.Provider>
  );
};
