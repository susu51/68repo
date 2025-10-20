import React, { createContext, useContext, useEffect, useState } from "react";
import api from "../api/http";

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
        const result = await api.get("/me");  // Use http.js get() which returns {data: ...}
        
        if (mounted && result?.data) {
          setUser(result.data);
          console.log('✅ User authenticated on mount:', result.data.email, result.data.role);
        } else {
          console.log('ℹ️ No authenticated user');
          setUser(null);
        }
      } catch (error) {
        console.log('ℹ️ No auth cookie found:', error.message);
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
      const result = await api.get("/me");
      
      if (result?.data) {
        setUser(result.data);
        console.log('✅ Auth status verified via cookie');
        return result.data;
      } else {
        setUser(null);
        return null;
      }
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
      const loginResult = await api.post("/auth/login", { email, password });

      if (!loginResult?.data) {
        throw new Error('Login failed');
      }

      // Get user data after successful login
      const meResult = await api.get("/me");
      
      if (meResult?.data) {
        setUser(meResult.data);
        console.log('✅ Login successful via cookie:', meResult.data.email);
        return { success: true, user: meResult.data };
      } else {
        throw new Error('Failed to fetch user data after login');
      }
    } catch (error) {
      console.error('❌ Login failed:', error);
      return { success: false, error: error.message || 'Login failed' };
    }
  };

  const logout = async () => {
    try {
      await api.post("/auth/logout", {});
      setUser(null);
      console.log('✅ Logout successful - cookies cleared');
    } catch (error) {
      console.error('❌ Logout error:', error);
      setUser(null);
    }
  };

  const register = async (userData) => {
    try {
      const result = await api.post("/auth/register", userData);

      if (!result?.data) {
        throw new Error('Registration failed');
      }

      console.log('✅ Registration successful');
      
      // Auto-login after registration
      if (result.data.user) {
        setUser(result.data.user);
        console.log('✅ User auto-logged in after registration');
      }
      
      return { success: true, user: result.data.user };
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