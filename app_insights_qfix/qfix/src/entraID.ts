import { PublicClientApplication } from "@azure/msal-browser";
import { EntraIDAuthority, EntraIDClientID } from "./config";

export const msalInstance = new PublicClientApplication({
    auth: {
      clientId:EntraIDClientID,
      authority: EntraIDAuthority,
      redirectUri: window.location.origin,
    },
    cache: {
      cacheLocation: 'localStorage',
      storeAuthStateInCookie: false,
    },
  });
  
  