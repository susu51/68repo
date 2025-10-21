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
  const connectingRef = useRef(false); // Single-flight guard
  const closedByUs = useRef(false); // Track intentional closure

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
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
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

  const connect = useCallback(() => {
    // SINGLE-FLIGHT GUARD: Prevent multiple simultaneous connection attempts
    if (connectingRef.current || wsRef.current) {
      console.log('⚠️ Connection already in progress or active, skipping...');
      return;
    }
    
    if (!businessId) {
      console.log('⚠️ No business ID provided for WebSocket');
      return;
    }
    
    // Pause reconnect when tab is hidden (battery-friendly)
    if (document.visibilityState === 'hidden') {
      console.log('📱 Tab hidden - pausing reconnect');
      connectingRef.current = false;
      // Will reconnect when tab becomes visible (handled by visibility listener)
      return;
    }

    connectingRef.current = true;
    closedByUs.current = false;

    try {
      // Construct WebSocket URL
      const backendUrl = process.env.REACT_APP_BACKEND_URL || '';
      
      // Determine protocol and host
      let wsUrl;
      
      if (backendUrl) {
        // Use backend URL if provided (prefer wss:// for prod)
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

      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('✅ WebSocket connected');
        setIsConnected(true);
        reconnectAttempts.current = 0;
        connectionStartTimeRef.current = Date.now();
        
        // Start heartbeat
        startHeartbeat(ws);
        
        // Reset backoff after 2 minutes of stable connection
        backoffResetTimeoutRef.current = setTimeout(() => {
          console.log('✅ 2-min stable connection - resetting backoff');
          reconnectAttempts.current = 0;
        }, 120000);
        
        // Send re-subscribe message (important after reconnect)
        ws.send(JSON.stringify({
          type: 'subscribe',
          business_id: businessId,
          role: 'business'
        }));
      };

      ws.onmessage = (event) => {
        try {
          // Handle pong response
          if (event.data === 'pong') {
            console.log('🏓 Received pong');
            missedPongsRef.current = 0;
            
            // Clear pong timeout
            if (pongTimeoutRef.current) {
              clearTimeout(pongTimeoutRef.current);
              pongTimeoutRef.current = null;
            }
            return;
          }
          
          const data = JSON.parse(event.data);
          console.log('📩 WebSocket message:', data);

          setLastEvent(data);

          if (data.type === 'order_notification' && data.data?.event_type === 'order.created') {
            // New order received!
            const orderInfo = data.data.data;
            
            // Play notification sound
            try {
              import('../utils/notificationSound').then(module => {
                module.default();
              });
            } catch (e) {
              console.log('Audio notification failed:', e);
            }

            // Show toast notification
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

      ws.onclose = (event) => {
        console.log(`🔌 WebSocket disconnected (code: ${event.code}, reason: ${event.reason || 'none'})`);
        setIsConnected(false);
        cleanupTimers();

        // Log abnormal closures for monitoring
        if (event.code === 1006 || event.code === 1011) {
          console.error(`🚨 Abnormal WebSocket closure: ${event.code} - business_id: ${businessId}`);
          // TODO: Send to Sentry with panel & businessId tags
        }

        // Exponential backoff: 1→2→4→8→16→max 30s with jitter
        const baseDelay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        const jitter = Math.random() * 1000; // 0-1s jitter
        const delay = baseDelay + jitter;
        
        console.log(`🔄 Reconnecting in ${(delay/1000).toFixed(1)}s... (attempt ${reconnectAttempts.current + 1})`);
        
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttempts.current += 1;
          connect();
        }, delay);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('❌ WebSocket connection error:', error);
    }
  }, [businessId, onOrderReceived, startHeartbeat, cleanupTimers]);

  const disconnect = useCallback(() => {
    cleanupTimers();
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    setIsConnected(false);
  }, [cleanupTimers]);

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
