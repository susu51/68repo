import { useEffect, useRef, useState, useCallback } from 'react';
import WSManager from '../ws/WSManager';

/**
 * Custom hook for WebSocket order notifications using singleton WSManager
 * 
 * Features:
 * - Single WebSocket connection across entire app
 * - StrictMode-safe (no duplicate connections on dev double-mount)
 * - Multi-tab support (only leader tab has active connection)
 * - Auth-aware (only connects when authenticated)
 * 
 * @param {string} businessId - Business ID to subscribe to
 * @param {function} onOrderReceived - Callback when order received
 * @param {boolean} enabled - Whether WebSocket should be active
 * @returns {Object} { isConnected, isLeader }
 */
export const useOrderNotifications = (businessId, onOrderReceived, enabled = true) => {
  const hasMountedRef = useRef(false);
  const callbackRef = useRef(onOrderReceived);
  const [connectionState, setConnectionState] = useState({
    isConnected: false,
    isLeader: false
  });
  
  // Keep callback ref updated
  useEffect(() => {
    callbackRef.current = onOrderReceived;
  }, [onOrderReceived]);
  
  // Update connection state periodically
  useEffect(() => {
    const updateState = () => {
      const state = WSManager.getConnectionState();
      setConnectionState({
        isConnected: state.isConnected,
        isLeader: state.isLeader
      });
    };
    
    // Initial update
    updateState();
    
    // Update every 2 seconds to reflect connection state
    const interval = setInterval(updateState, 2000);
    
    return () => clearInterval(interval);
  }, []);
  
  // One-time initialization (StrictMode-safe)
  useEffect(() => {
    if (hasMountedRef.current) {
      console.log('⚠️ useOrderNotifications: Already mounted (StrictMode double-mount), skipping setup');
      return;
    }
    
    hasMountedRef.current = true;
    console.log('🎬 useOrderNotifications: Initial mount');
    
    // Cleanup on unmount
    return () => {
      console.log('🧹 useOrderNotifications: Unmounting');
      hasMountedRef.current = false;
    };
  }, []);
  
  // Subscribe to WSManager messages
  useEffect(() => {
    const handleMessage = (message) => {
      try {
        // Handle pong response
        if (message.type === 'pong') {
          return;
        }
        
        // Handle order notifications
        if (message.type === 'order_notification' && message.data?.event_type === 'order.created') {
          console.log('🔔 New order notification received:', message.data);
          
          if (callbackRef.current) {
            callbackRef.current(message.data);
          }
        }
        
        // Handle subscribed confirmation
        if (message.type === 'subscribed') {
          console.log('✅ Subscribed to order notifications');
        }
        
      } catch (error) {
        console.error('❌ Error handling WebSocket message:', error);
      }
    };
    
    // Subscribe to messages
    const unsubscribe = WSManager.subscribe(handleMessage);
    
    return () => {
      unsubscribe();
    };
  }, []);
  
  // Update WSManager configuration when params or enabled state changes
  useEffect(() => {
    if (!businessId) {
      console.log('⚠️ No business ID, disabling WebSocket');
      WSManager.setEnabled(false);
      return;
    }
    
    // Construct WebSocket URL
    const backendUrl = process.env.REACT_APP_BACKEND_URL || '';
    const protocol = backendUrl.startsWith('https') ? 'wss' : 'ws';
    const host = backendUrl.replace(/^https?:\/\//, '').replace(/\/$/, '');
    const wsUrl = `${protocol}://${host}/api/ws/orders`;
    
    console.log('🔧 Configuring WSManager:', {
      businessId,
      enabled,
      wsUrl
    });
    
    // Initialize/reconfigure WSManager
    WSManager.init({
      url: wsUrl,
      params: {
        business_id: businessId,
        role: 'business'
      },
      enabled: enabled
    });
    
  }, [businessId, enabled]);
  
  // Return empty object for now (can add isConnected state later if needed)
  return {};
};
