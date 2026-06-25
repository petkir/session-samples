import { MantineProvider, ColorSchemeScript, createTheme, MantineColorScheme } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import { MsalProvider } from '@azure/msal-react';
import { PublicClientApplication } from '@azure/msal-browser';
import { ThemeProvider } from './contexts/ThemeContext';
import { useAuth } from './hooks/useAuth';
import { useTheme } from './hooks/useTheme';
import ChatInterface from './components/ChatInterface';
import Login from './components/Login';
import Loading from './components/Loading';
import AppHeader from './components/AppHeader';
import { msalConfig } from './authConfig';
import { setTokenProvider } from './services/chatApi';
import { useEffect } from 'react';
import './App.scss';
import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';

const theme = createTheme({
    primaryColor: 'blue',
    fontFamily: '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif',
});

// Create MSAL instance
const msalInstance = new PublicClientApplication(msalConfig);

function AppContent() {
    const { isLoading, login, logout, isAuthenticated, user, getAccessToken } = useAuth();

    // Set up token provider for API calls
    useEffect(() => {
        setTokenProvider(getAccessToken);
    }, [getAccessToken]);

    if (isLoading) {
        return <Loading />;
    }

    const handleSwitchUser = () => {
        logout();
        // This will cause the component to re-render and show the login screen
    };

    if (!isAuthenticated) {
        return (
            <>
                <AppHeader />
                <Login onLogin={login} />
            </>
        );
    }

    return (
        <>
            <AppHeader 
                user={user} 
                onLogout={logout}
                onSwitchUser={handleSwitchUser}
            />
            <ChatInterface />
        </>
    );
}

function MantineApp() {
    const { colorScheme } = useTheme();
    
    return (
        <MantineProvider 
            theme={theme} 
            defaultColorScheme={colorScheme as MantineColorScheme} 
            forceColorScheme={colorScheme}
        >
            <Notifications />
            <div className="app">
                <AppContent />
            </div>
        </MantineProvider>
    );
}

function App() {
    return (
        <>
            <ColorSchemeScript defaultColorScheme="auto" />
            <MsalProvider instance={msalInstance}>
                <ThemeProvider>
                    <MantineApp />
                </ThemeProvider>
            </MsalProvider>
        </>
    );
}

export default App;