import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import { appInsights } from './appInsights';
import { Providers } from "@microsoft/mgt-element";
import { Msal2Provider } from "@microsoft/mgt-msal2-provider";



const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

Providers.globalProvider = new Msal2Provider({
  clientId: 'REPLACE_WITH_CLIENTID'
});

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
