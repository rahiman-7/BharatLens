import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { User, LoginCredentials, RegisterCredentials } from './authTypes';

import { loginApi, registerApi, getMeApi } from './authApi';

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const TOKEN_KEY = 'bharatlens_token';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem(TOKEN_KEY);
    }
    return null;
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Validate existing token on mount
  useEffect(() => {
    async function loadUser() {
      if (!token) {
        setIsLoading(false);
        return;
      }
      try {
        const currentUser = await getMeApi();
        setUser(currentUser);
      } catch {
        // Token invalid or expired
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    }
    loadUser();
  }, [token]);

  const login = useCallback(async (credentials: LoginCredentials) => {
    setIsLoading(true);
    try {
      const data = await loginApi(credentials);
      localStorage.setItem(TOKEN_KEY, data.access_token);
      setToken(data.access_token);
      setUser(data.user);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (credentials: RegisterCredentials) => {
    setIsLoading(true);
    try {
      await registerApi(credentials);
      // Auto login after successful registration
      const data = await loginApi(credentials);
      localStorage.setItem(TOKEN_KEY, data.access_token);
      setToken(data.access_token);
      setUser(data.user);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const value: AuthContextValue = {
    user,
    token,
    isAuthenticated: !!user && !!token,
    isLoading,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
