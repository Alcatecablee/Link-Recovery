import React, { createContext, useContext, useState, useEffect } from 'react';
import { auth } from '@/api/client';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState({ id: 'demo-user', email: 'demo@example.com', name: 'Demo User' });
  const [isAuthenticated, setIsAuthenticated] = useState(true);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    autoLogin();
  }, []);

  const autoLogin = async () => {
    try {
      await auth.demoLogin();
    } catch (error) {
      console.log('Auto-login:', error.message);
    }
  };

  const login = async () => {
    return true;
  };

  const logout = async () => {
    try {
      await auth.logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const value = {
    user,
    isAuthenticated,
    loading,
    login,
    logout
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
