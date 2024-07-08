import React, { useEffect } from 'react';

import './App.css';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import Header from './components/Header';
import { ThemeProvider } from '@fluentui/react';
import Home from './pages/Home';
import { reactPlugin } from './appInsights';
import { withAITracking } from '@microsoft/applicationinsights-react-js';
import { positionTrackingService } from './services/PositionTrackingService';
import ReportIssuePage from './pages/ReportIssuePage';



const App: React.FC = () => {
  useEffect(() => {
    positionTrackingService.startTracking();

    return () => {
      positionTrackingService.stopTracking();
    };
  }, []);

  return (
    <ThemeProvider>
    <BrowserRouter>
      <Header />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/report-issue" element={<ReportIssuePage />} />
      </Routes>
    </BrowserRouter>
  </ThemeProvider>
  );
};

export default withAITracking(reactPlugin, App);
