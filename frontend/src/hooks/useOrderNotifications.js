import { useEffect, useRef, useState, useCallback } from 'react';
import { toast } from 'react-hot-toast';

/**
 * Custom hook for WebSocket order notifications
 * @param {string} businessId - Business ID to subscribe to
 * @param {function} onOrderReceived - Callback when new order received
 */
export const useOrderNotifications = (businessId, onOrderReceived) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);

  const connect = useCallback(() => {
    if (!businessId) {
      console.log('⚠️ No business ID provided for WebSocket');
      console.log('businessId:', businessId);
      return;
    }

    try {
      // Construct WebSocket URL
      const backendUrl = process.env.REACT_APP_BACKEND_URL || '';
      
      // Determine protocol (wss for https, ws for http)
      let protocol = 'ws:';
      let host = window.location.host;
      
      if (backendUrl) {
        // Use backend URL if provided
        protocol = backendUrl.startsWith('https') ? 'wss:' : 'ws:';
        host = backendUrl.replace(/^https?:\/\//, '');
      } else if (window.location.protocol === 'https:') {
        protocol = 'wss:';
      }
      
      const wsUrl = `${protocol}//${host}/api/ws/orders?business_id=${businessId}&role=business`;

      console.log('🔌 Connecting to WebSocket:');
      console.log('   Protocol:', protocol);
      console.log('   Host:', host);
      console.log('   Full URL:', wsUrl);
      console.log('   Business ID:', businessId);
      console.log('   Backend URL:', backendUrl);

      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('✅ WebSocket connected');
        setIsConnected(true);
        reconnectAttempts.current = 0;
        
        // Send ping every 30 seconds to keep connection alive
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, 30000);

        ws.pingInterval = pingInterval;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📩 WebSocket message:', data);

          setLastEvent(data);

          if (data.type === 'order_notification' && data.data?.event_type === 'order.created') {
            // New order received!
            const orderInfo = data.data.data;
            
            // Play notification sound
            try {
              // Use utility function for sound
              import('../utils/notificationSound').then(module => {
                module.default();
              });
            } catch (e) {
              console.log('Audio notification failed:', e);
            }

            // Show toast notification with enhanced styling
            toast.success(
              `🆕 Yeni Sipariş!\n${orderInfo.customer_name}\n${orderInfo.total} TL`,
              {
                duration: 10000,
                icon: '🔔',
                style: {
                  background: '#10b981',
                  color: 'white',
                  fontSize: '16px',
                  fontWeight: 'bold',
                  border: '2px solid #059669',
                  boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
                }
              }
            );

            // Call callback
            if (onOrderReceived) {
              onOrderReceived(data.data);
            }
          }
        } catch (error) {
          console.error('❌ Error parsing WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
      };

      ws.onclose = () => {
        console.log('🔌 WebSocket disconnected');
        setIsConnected(false);

        // Clear ping interval
        if (ws.pingInterval) {
          clearInterval(ws.pingInterval);
        }

        // Attempt to reconnect with exponential backoff
        if (reconnectAttempts.current < 5) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
          console.log(`🔄 Reconnecting in ${delay}ms... (attempt ${reconnectAttempts.current + 1})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current += 1;
            connect();
          }, delay);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('❌ WebSocket connection error:', error);
    }
  }, [businessId, onOrderReceived]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      // Clear ping interval
      if (wsRef.current.pingInterval) {
        clearInterval(wsRef.current.pingInterval);
      }
      
      wsRef.current.close();
      wsRef.current = null;
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    setIsConnected(false);
  }, []);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return {
    isConnected,
    lastEvent,
    reconnect: connect
  };
};
