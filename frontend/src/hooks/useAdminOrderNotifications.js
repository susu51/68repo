import { useEffect, useRef, useState, useCallback } from 'react';

/**
 * Custom hook for Admin to receive real-time order notifications via WebSocket
 * Connects to backend WebSocket and listens for ALL order events
 */
const useAdminOrderNotifications = (onNewOrder) => {
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionAttempts, setConnectionAttempts] = useState(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    try {
      // Get backend URL from environment
      let backendUrl = process.env.REACT_APP_BACKEND_URL || 'https://admin-wsocket.preview.emergentagent.com';
      
      // Ensure /api is included in the URL
      if (!backendUrl.endsWith('/api')) {
        backendUrl = `${backendUrl}/api`;
      }
      
      // Convert http/https to ws/wss
      const wsUrl = backendUrl
        .replace('https://', 'wss://')
        .replace('http://', 'ws://');
      
      // Admin WebSocket connection (no business_id needed)
      // WebSocket endpoint is at /api/ws/orders
      const websocketUrl = `${wsUrl}/ws/orders?role=admin`;
      
      console.log('🔌 Admin connecting to WebSocket:', websocketUrl);
      
      const ws = new WebSocket(websocketUrl);
      
      ws.onopen = () => {
        console.log('✅ Admin WebSocket connected');
        setIsConnected(true);
        setConnectionAttempts(0);
        
        // Send ping every 30 seconds to keep connection alive
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, 30000);
        
        // Store interval for cleanup
        ws.pingInterval = pingInterval;
      };
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('📨 Admin received WebSocket message:', message);
          
          if (message.type === 'connected') {
            console.log('✅ Admin connection confirmed:', message.message);
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
      
      ws.onclose = () => {
        console.log('🔌 Admin WebSocket disconnected');
        setIsConnected(false);
        
        // Clear ping interval
        if (ws.pingInterval) {
          clearInterval(ws.pingInterval);
        }
        
        // Attempt to reconnect
        if (connectionAttempts < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, connectionAttempts), 30000);
          console.log(`⏳ Reconnecting admin WebSocket in ${delay}ms...`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            setConnectionAttempts(prev => prev + 1);
            connect();
          }, delay);
        } else {
          console.error('❌ Max admin WebSocket reconnection attempts reached');
        }
      };
      
      wsRef.current = ws;
      
    } catch (error) {
      console.error('❌ Error creating admin WebSocket connection:', error);
      setIsConnected(false);
    }
  }, [onNewOrder, connectionAttempts]);

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
