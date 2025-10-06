import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { apiClient } from '../utils/apiClient';

// Auth Context with default values
const AuthContext = createContext({
  user: null,
  token: null,
  isAuthenticated: false,
  login: () => {},
  logout: () => {},
  updateUser: () => {},
  isLoading: true
});

// Auth Provider Component  
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize auth state from existing localStorage (one-time migration)
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        // ONE-TIME MIGRATION: Read existing localStorage data
        const existingToken = localStorage.getItem('kuryecini_access_token');
        const existingUser = localStorage.getItem('kuryecini_user');
        
        if (existingToken && existingUser) {
          const parsedUser = JSON.parse(existingUser);
          
          // Set in context
          setToken(existingToken);
          setUser(parsedUser);
          
          // Set axios default authorization header
          axios.defaults.headers.common['Authorization'] = `Bearer ${existingToken}`;
          
          // CLEAN UP localStorage after migration
          localStorage.removeItem('kuryecini_access_token');
          localStorage.removeItem('kuryecini_user');
          
          console.log('✅ Auth migrated from localStorage to Context API');
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
        // Clear any corrupted data
        localStorage.removeItem('kuryecini_access_token');
        localStorage.removeItem('kuryecini_user');
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, []);

  // Login function
  const login = useCallback((authData) => {
    try {
      const userToken = authData.access_token;
      const userData = authData.user || authData.user_data;
      
      setToken(userToken);
      setUser(userData);
      
      // Set axios default authorization header and apiClient token
      axios.defaults.headers.common['Authorization'] = `Bearer ${userToken}`;
      apiClient.setToken(userToken);
      
      console.log('✅ User logged in via Context API');
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }, []);

  // Logout function
  const logout = useCallback(() => {
    try {
      setToken(null);
      setUser(null);
      
      // Remove axios authorization header and apiClient token
      delete axios.defaults.headers.common['Authorization'];
      apiClient.setToken(null);
      
      console.log('✅ User logged out via Context API');
    } catch (error) {
      console.error('Logout error:', error);
    }
  }, []);

  // Update user function
  const updateUser = useCallback((userData) => {
    setUser(userData);
  }, []);

  // Computed properties
  const isAuthenticated = !!token && !!user;

  // Context value
  const value = React.useMemo(() => ({
    user,
    token,
    isAuthenticated,
    isLoading,
    login,
    logout,
    updateUser
  }), [user, token, isAuthenticated, isLoading, login, logout, updateUser]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// Custom hook to use auth context
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;