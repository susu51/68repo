import { useEffect, useRef, useState, useCallback } from 'react';

/**
 * Custom hook for Admin to receive real-time order notifications via WebSocket
 * Connects to backend WebSocket and listens for ALL order events
 * 
 * Heartbeat: Ping every 25s, expect pong within 5s, close & reconnect if missed twice
 * Reconnect: Exponential backoff 1→2→4→8→16→max 30s with jitter
 * Reset backoff after stable 2-minute connection
 */
const useAdminOrderNotifications = (onNewOrder) => {
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionAttempts, setConnectionAttempts] = useState(0);
  const pingIntervalRef = useRef(null);
  const pongTimeoutRef = useRef(null);
  const missedPongsRef = useRef(0);
  const connectionStartTimeRef = useRef(null);
  const backoffResetTimeoutRef = useRef(null);


  const cleanupTimers = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
    if (pongTimeoutRef.current) {
      clearTimeout(pongTimeoutRef.current);
      pongTimeoutRef.current = null;
    }
    if (backoffResetTimeoutRef.current) {
      clearTimeout(backoffResetTimeoutRef.current);
      backoffResetTimeoutRef.current = null;
    }
  }, []);

  const startHeartbeat = useCallback((ws) => {
    cleanupTimers();
    missedPongsRef.current = 0;
    
    // Send ping every 25s
    pingIntervalRef.current = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        console.log('📡 Admin sending ping');
        ws.send('ping');
        
        // Wait for pong (5s timeout)
        pongTimeoutRef.current = setTimeout(() => {
          missedPongsRef.current += 1;
          console.warn(`⚠️ Admin pong timeout (missed: ${missedPongsRef.current}/2)`);
          
          // Close & reconnect if missed twice
          if (missedPongsRef.current >= 2) {
            console.error('❌ Admin missed 2 pongs - closing connection');
            ws.close(1000, 'Heartbeat failure');
          }
        }, 5000);
      }
    }, 25000);
  }, [cleanupTimers]);

  const connect = useCallback(() => {
    try {
      // Get backend URL from environment
      let backendUrl = process.env.REACT_APP_BACKEND_URL || 'https://ai-order-debug.preview.emergentagent.com';
      
      // Ensure /api is included in the URL
      if (!backendUrl.endsWith('/api')) {
        backendUrl = `${backendUrl}/api`;
      }
      
      // Convert http/https to ws/wss (prefer wss for prod)
      const wsUrl = backendUrl
        .replace('https://', 'wss://')
        .replace('http://', 'ws://');
      
      // Admin WebSocket connection
      const websocketUrl = `${wsUrl}/ws/orders?role=admin`;
      
      console.log('🔌 Admin connecting to WebSocket:', websocketUrl);
      
      const ws = new WebSocket(websocketUrl);
      
      ws.onopen = () => {
        console.log('✅ Admin WebSocket connected successfully');
        setIsConnected(true);
        setConnectionAttempts(0);
        connectionStartTimeRef.current = Date.now();
        
        // Start heartbeat
        startHeartbeat(ws);
        
        // Reset backoff after 2 minutes of stable connection
        backoffResetTimeoutRef.current = setTimeout(() => {
          console.log('✅ Admin 2-min stable connection - resetting backoff');
          setConnectionAttempts(0);
        }, 120000);
        
        // Send re-subscribe message
        ws.send(JSON.stringify({
          type: 'subscribe',
          role: 'admin'
        }));
      };
      
      ws.onmessage = (event) => {
        try {
          // Handle pong response
          if (event.data === 'pong') {
            console.log('🏓 Admin received pong');
            missedPongsRef.current = 0;
            
            // Clear pong timeout
            if (pongTimeoutRef.current) {
              clearTimeout(pongTimeoutRef.current);
              pongTimeoutRef.current = null;
            }
            return;
          }
          
          console.log('📨 Admin WebSocket raw message:', event.data);
          
          const message = JSON.parse(event.data);
          console.log('📨 Admin received WebSocket message:', message);
          
          if (message.type === 'connected') {
            console.log('✅ Admin connection confirmed:', message.message);
          } else if (message.type === 'subscribed') {
            console.log('✅ Admin re-subscribed successfully');
          } else if (message.type === 'order_notification') {
            console.log('🆕 New order notification for admin:', message.data);
            
            // Call the callback with new order data
            if (onNewOrder && typeof onNewOrder === 'function') {
              onNewOrder(message.data);
            }
          }
        } catch (error) {
          console.error('❌ Error parsing WebSocket message:', error);
        }
      };
      
      ws.onerror = (error) => {
        console.error('❌ Admin WebSocket error:', error);
        setIsConnected(false);
      };
      
      ws.onclose = (event) => {
        console.log(`🔌 Admin WebSocket disconnected (code: ${event.code}, reason: ${event.reason || 'none'})`);
        setIsConnected(false);
        cleanupTimers();
        
        // Log abnormal closures
        if (event.code === 1006 || event.code === 1011) {
          console.error(`🚨 Admin abnormal WebSocket closure: ${event.code}`);
          // TODO: Send to Sentry with panel=admin tag
        }
        
        // Exponential backoff: 1→2→4→8→16→max 30s with jitter
        const baseDelay = Math.min(1000 * Math.pow(2, connectionAttempts), 30000);
        const jitter = Math.random() * 1000;
        const delay = baseDelay + jitter;
        
        console.log(`⏳ Reconnecting admin WebSocket in ${(delay/1000).toFixed(1)}s... (attempt ${connectionAttempts + 1})`);
        
        reconnectTimeoutRef.current = setTimeout(() => {
          setConnectionAttempts(prev => prev + 1);
          connect();
        }, delay);
      };
      
      wsRef.current = ws;
      
    } catch (error) {
      console.error('❌ Error creating admin WebSocket connection:', error);
      setIsConnected(false);
    }
  }, [onNewOrder, connectionAttempts, startHeartbeat, cleanupTimers]);

  useEffect(() => {
    // Connect on mount
    connect();

    // Cleanup on unmount
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      
      if (wsRef.current) {
        // Clear ping interval
        if (wsRef.current.pingInterval) {
          clearInterval(wsRef.current.pingInterval);
        }
        
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run on mount/unmount, not when connect changes

  return { isConnected };
};

export default useAdminOrderNotifications;
