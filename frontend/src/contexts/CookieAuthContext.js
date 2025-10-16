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
  const [loading, setLoading] = useState(true);  // Start with true for initial check
  const [ready, setReady] = useState(false);  // Start with false

  // Check auth status on mount
  useEffect(() => {
    let mounted = true;
    
    const initAuth = async () => {
      try {
        console.log('🔍 Checking initial auth status...');
        const response = await api("/me");  // Use /api/me instead of /api/auth/me
        
        if (mounted && response.ok) {
          const userData = await response.json();
          setUser(userData);
          console.log('✅ User authenticated on mount:', userData.email, userData.role);
        } else {
          console.log('ℹ️ No authenticated user');
          setUser(null);
        }
      } catch (error) {
        console.log('ℹ️ No auth cookie found');
        if (mounted) setUser(null);
      } finally {
        if (mounted) {
          setLoading(false);
          setReady(true);
        }
      }
    };
    
    initAuth();
    
    return () => {
      mounted = false;
    };
  }, []);

  // Manual check for refresh
  const checkAuthStatus = async () => {
    try {
      setLoading(true);
      const response = await api("/me");  // Use /api/me instead of /api/auth/me
      const userData = await response.json();
      
      setUser(userData);
      console.log('✅ Auth status verified via cookie');
      return userData;
    } catch (error) {
      console.log('❌ No valid auth cookie found');
      setUser(null);
      return null;
    } finally {
      setLoading(false);
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
        throw new Error(error.detail || error.message || 'Login failed');
      }

      // Get user data after successful login
      const meResponse = await api("/me");  // Use /api/me instead of /api/auth/me
      const userData = await meResponse.json();
      
      setUser(userData);
      console.log('✅ Login successful via cookie');
      
      return { success: true, user: userData };
    } catch (error) {
      console.error('❌ Login failed:', error);
      // Return error in a format that UI can handle
      return { success: false, error: error.message || 'Login failed' };
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
      
      // Auto-login after registration - get user data
      if (result.success && result.user) {
        setUser(result.user);
        console.log('✅ User auto-logged in after registration');
      }
      
      return { success: true, user: result.user };
    } catch (error) {
      console.error('❌ Registration failed:', error);
      return { success: false, error: error.message || 'Registration failed' };
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