// DEPRECATED - Use CookieAuthContext instead
// This file maintained for compatibility during migration

import React, { createContext, useContext } from 'react';

const AuthContext = createContext();

export const useAuth = () => {
  console.warn('❌ DEPRECATED: useAuth from AuthContext is deprecated. Use useCookieAuth from CookieAuthContext instead.');
  
  // Fallback compatibility
  return {
    user: null,
    token: null,
    loading: false,
    isAuthenticated: false,
    login: async () => ({ success: false, error: 'Deprecated auth system' }),
    logout: () => console.warn('Use CookieAuthContext logout instead')
  };
};

export const AuthProvider = ({ children }) => {
  console.warn('❌ DEPRECATED: AuthProvider is deprecated. Use CookieAuthProvider instead.');
  
  const value = {
    user: null,
    token: null,
    loading: false,
    isAuthenticated: false,
    login: async () => ({ success: false, error: 'Deprecated auth system' }),
    logout: () => console.warn('Use CookieAuthContext logout instead')
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthProvider;