import React, { useEffect } from 'react';

import './App.css';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import Header from './components/Header';

import Home from './pages/Home';
import { reactPlugin } from './appInsights';
import { AppInsightsContext, AppInsightsErrorBoundary, withAITracking } from '@microsoft/applicationinsights-react-js';
import { positionTrackingService } from './services/PositionTrackingService';
import ReportIssuePage from './pages/ReportIssuePage';
import { ThemeProvider } from './contexts/ThemeProvider';
import { msalInstance } from './entraID';
import { QFixProvider } from './contexts/QFixProvider';
import { Stack } from '@fluentui/react';
import LocalIssuesPage from './pages/LocalIssuesPage';
import { LoginCheck } from './components/LoginChek';
import Datenschutz from './pages/Datenschutz';
import Footer from './components/Footer';



const App: React.FC = () => {
  const [init, setInit] = React.useState(false);


  useEffect(() => {
    async function initApp() {
      await (msalInstance as any).initialize();
      setInit(true);
    }
    positionTrackingService.startTracking();
    initApp();
    return () => {
      positionTrackingService.stopTracking();
    };
  }, []);

  return (
    <AppInsightsErrorBoundary onError={() => <h1>I believe something went wrong</h1>} appInsights={reactPlugin}>
      <AppInsightsContext.Provider value={reactPlugin}>
        <ThemeProvider>
          <BrowserRouter>
            <QFixProvider>
              <LoginCheck>
                <Header />
                {init && <Stack horizontalAlign="center" verticalAlign="center" styles={{ root: { height: 'calc( 100vh - 160px)', overflowY: 'scroll' } }} >
                  <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/report-issue" element={<ReportIssuePage />} />
                    <Route path="/unsubmitted-issue" element={<LocalIssuesPage />} />
                    <Route path="/datenrichtlinie" element={<Datenschutz />} />
                  </Routes>
                </Stack>}
                <Footer />
              </LoginCheck>
            </QFixProvider>
          </BrowserRouter>
        </ThemeProvider>
      </AppInsightsContext.Provider>
    </AppInsightsErrorBoundary>

  );
};

export default withAITracking(reactPlugin, App);
