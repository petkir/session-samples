import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import { appInsights } from './appInsights';

import { initializeIcons } from '@fluentui/font-icons-mdl2';




initializeIcons();

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);






root.render(
  <React.StrictMode>

    <App />

  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals

reportWebVitals((metric) => {
  appInsights.trackMetric({ name: metric.name, average: metric.value });
});

window.addEventListener('online', () => {
  // Implement logic to submit cached issues
  console.log('Device came back online, submitting cached issues...');
});
