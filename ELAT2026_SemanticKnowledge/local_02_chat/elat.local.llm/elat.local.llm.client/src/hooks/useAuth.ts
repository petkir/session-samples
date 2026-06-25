import { useMsal } from '@azure/msal-react';
import { loginRequest, apiRequest } from '../authConfig';
import { useEffect, useState } from 'react';

interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
}

export const useAuth = () => {
  const { instance, accounts } = useMsal();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (accounts.length > 0) {
      const account = accounts[0];
      setUser({
        id: account.localAccountId,
        name: account.name || '',
        email: account.username,
        avatar: `https://graph.microsoft.com/v1.0/me/photo/$value`
      });
    }
    setIsLoading(false);
  }, [accounts]);

  const getAccessToken = async (): Promise<string | null> => {
    try {
      if (accounts.length === 0) {
        return null;
      }

      const tokenRequest = {
        ...apiRequest,
        account: accounts[0],
      };

      const response = await instance.acquireTokenSilent(tokenRequest);
      return response.accessToken;
    } catch (error) {
      console.error('Token acquisition failed:', error);
      
      // Try to acquire token interactively if silent acquisition fails
      try {
        const tokenRequest = {
          ...apiRequest,
          account: accounts[0],
        };
        const response = await instance.acquireTokenPopup(tokenRequest);
        return response.accessToken;
      } catch (interactiveError) {
        console.error('Interactive token acquisition failed:', interactiveError);
        return null;
      }
    }
  };

  const login = async () => {
    try {
      await instance.loginPopup(loginRequest);
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  const logout = async () => {
    try {
      await instance.logoutPopup();
      setUser(null);
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return {
    user,
    isAuthenticated: !!user,
    isLoading,
    getAccessToken,
    login,
    logout
  };
};
