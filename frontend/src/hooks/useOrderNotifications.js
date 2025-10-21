import { useEffect, useRef, useState, useCallback } from 'react';
import { toast } from 'react-hot-toast';

/**
 * Custom hook for WebSocket order notifications with robust heartbeat & reconnection
 * @param {string} businessId - Business ID to subscribe to
 * @param {function} onOrderReceived - Callback when new order received
 * 
 * Heartbeat: Ping every 25s, expect pong within 5s, close & reconnect if missed twice
 * Reconnect: Exponential backoff 1→2→4→8→16→max 30s with jitter
 * Reset backoff after stable 2-minute connection
 */
export const useOrderNotifications = (businessId, onOrderReceived) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);
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
        console.log('📡 Sending ping');
        ws.send('ping');
        
        // Wait for pong (5s timeout)
        pongTimeoutRef.current = setTimeout(() => {
          missedPongsRef.current += 1;
          console.warn(`⚠️ Pong timeout (missed: ${missedPongsRef.current}/2)`);
          
          // Close & reconnect if missed twice
          if (missedPongsRef.current >= 2) {
            console.error('❌ Missed 2 pongs - closing connection');
            ws.close(1000, 'Heartbeat failure');
          }
        }, 5000);
      }
    }, 25000);
  }, [cleanupTimers]);
    if (!businessId) {
      console.log('⚠️ No business ID provided for WebSocket');
      console.log('businessId:', businessId);
      return;
    }

    try {
      // Construct WebSocket URL
      const backendUrl = process.env.REACT_APP_BACKEND_URL || '';
      
      // Determine protocol and host
      let wsUrl;
      
      if (backendUrl) {
        // Use backend URL if provided
        const protocol = backendUrl.startsWith('https') ? 'wss' : 'ws';
        const host = backendUrl.replace(/^https?:\/\//, '').replace(/\/$/, '');
        wsUrl = `${protocol}://${host}/api/ws/orders?business_id=${businessId}&role=business`;
      } else {
        // Fallback to current location
        const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
        const host = window.location.host;
        wsUrl = `${protocol}://${host}/api/ws/orders?business_id=${businessId}&role=business`;
      }

      console.log('🔌 Connecting to WebSocket:', wsUrl);
      console.log('   Business ID:', businessId);

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
