import React, {  useEffect } from 'react';

import './App.css';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import Header from './components/Header';

import Home from './pages/Home';
import { reactPlugin } from './appInsights';
import { withAITracking } from '@microsoft/applicationinsights-react-js';
import { positionTrackingService } from './services/PositionTrackingService';
import ReportIssuePage from './pages/ReportIssuePage';
import { ThemeProvider } from './contexts/ThemeProvider';
import { msalInstance } from './entraID';
import { QFixProvider } from './contexts/QFixProvider';
import { Stack } from '@fluentui/react';
import LocalIssuesPage from './pages/LocalIssuesPage';



const App: React.FC = () => {
  const[init, setInit] = React.useState(false);

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
  
    <ThemeProvider>
    <BrowserRouter>
    <QFixProvider>
  <Header />
  {init&&<Stack horizontalAlign="center" verticalAlign="center" >
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/report-issue" element={<ReportIssuePage />} />
        <Route path="/unsubmitted-issue" element={<LocalIssuesPage   />} />
      </Routes>
      </Stack>}
      </QFixProvider>
    </BrowserRouter>
  </ThemeProvider>
  
  );
};

export default withAITracking(reactPlugin, App);
