import React, { createContext, useContext, useEffect, useState } from "react";
import { api } from "../api/http";

// Cookie-based Auth Context - NO localStorage
const CookieAuthContext = createContext(null);

export const useCookieAuth = () => {
  const context = useContext(CookieAuthContext);
  if (!context) {
    throw new Error('useCookieAuth must be used within CookieAuthProvider');
  }
  return context;
};

export const CookieAuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [ready, setReady] = useState(false);

  // Check auth status on mount
  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      setLoading(true);
      const response = await api("/auth/me");
      const userData = await response.json();
      
      setUser(userData);
      console.log('✅ Auth status verified via cookie');
    } catch (error) {
      console.log('❌ No valid auth cookie found');
      setUser(null);
    } finally {
      setLoading(false);
      setReady(true);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await api("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
      }

      // Get user data after successful login
      const meResponse = await api("/auth/me");
      const userData = await meResponse.json();
      
      setUser(userData);
      console.log('✅ Login successful via cookie');
      
      return { success: true, user: userData };
    } catch (error) {
      console.error('❌ Login failed:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      await api("/auth/logout", { method: "POST" });
      setUser(null);
      console.log('✅ Logout successful - cookies cleared');
    } catch (error) {
      console.error('❌ Logout error:', error);
      // Still clear user state
      setUser(null);
    }
  };

  const register = async (userData) => {
    try {
      const response = await api("/auth/register", {
        method: "POST",
        body: JSON.stringify(userData)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Registration failed');
      }

      const result = await response.json();
      console.log('✅ Registration successful');
      
      return result;
    } catch (error) {
      console.error('❌ Registration failed:', error);
      throw error;
    }
  };

  // Context value
  const value = {
    user,
    loading,
    ready,
    isAuthenticated: !!user,
    login,
    logout,
    register,
    checkAuthStatus
  };

  return (
    <CookieAuthContext.Provider value={value}>
      {children}
    </CookieAuthContext.Provider>
  );
};

export default CookieAuthProvider;