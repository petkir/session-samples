import { Configuration } from '@azure/msal-browser';

// Get configuration from environment variables
const clientId = import.meta.env.VITE_AZURE_CLIENT_ID;
const tenantId = import.meta.env.VITE_AZURE_TENANT_ID;

if (!clientId || !tenantId) {
  throw new Error('Missing required Azure AD configuration. Please check your .env file.');
}

export const msalConfig: Configuration = {
  auth: {
    clientId: clientId,
    authority: `https://login.microsoftonline.com/${tenantId}`,
    redirectUri: window.location.origin,
  },
  cache: {
    cacheLocation: 'localStorage',
    storeAuthStateInCookie: false,
  },
};

export const loginRequest = {
  scopes: ['openid', 'profile', 'User.Read'],
};

// API scopes for accessing our backend
export const apiRequest = {
  scopes: [`api://${clientId}/access_as_user`],
};
