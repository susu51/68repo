/**
 * WSManager - Singleton WebSocket Manager
 * 
 * Features:
 * - Single WebSocket connection per browser context
 * - Multi-tab leader election via BroadcastChannel
 * - Exponential backoff reconnection (1s → 30s)
 * - Heartbeat ping every 25s
 * - Visibility-aware (pause when hidden)
 * - Auth-aware (only connect when enabled)
 */

class WSManager {
  constructor() {
    // WebSocket state
    this.ws = null;
    this.subscribers = new Set();
    this.enabled = false;
    this.attempt = 0;
    this.pingTimer = null;
    this.reconnectTimer = null;
    this.created = false;
    
    // Configuration
    this.config = {
      url: '',
      params: {}
    };
    
    // Multi-tab leadership
    this.channel = null;
    this.isLeader = false;
    this.leaderHeartbeatTimer = null;
    
    // Guards
    this.connecting = false;
  }
  
  /**
   * Initialize WSManager with URL and params
   * @param {Object} options - { url, params, enabled }
   */
  init({ url, params = {}, enabled = false }) {
    this.config = { url, params };
    this.setEnabled(enabled);
    
    // One-time setup
    if (!this.created) {
      this.created = true;
      this.setupBroadcast();
      this.setupVisibilityListener();
    }
  }
  
  /**
   * Setup BroadcastChannel for multi-tab communication
   */
  setupBroadcast() {
    try {
      this.channel = new BroadcastChannel('kuryecini-ws');
      
      this.channel.onmessage = (event) => {
        const { type, payload } = event.data || {};
        
        if (type === 'ws-broadcast') {
          // Follower tabs receive messages from leader
          if (!this.isLeader) {
            this.notifySubscribers(payload);
          }
        } else if (type === 'leader-gone') {
          // Leader resigned, try to become new leader
          if (!this.isLeader && this.enabled) {
            console.log('👑 Previous leader gone, attempting to become leader');
            this.becomeLeader();
          }
        } else if (type === 'leader-heartbeat') {
          // Another tab is claiming leadership
          if (this.isLeader && event.data.timestamp > Date.now() - 5000) {
            console.log('👑 Another tab is leader, resigning');
            this.resignLeader();
          }
        }
      };
      
      // Try to become leader on init
      setTimeout(() => this.becomeLeader(), 100);
      
      // Notify other tabs when closing
      window.addEventListener('beforeunload', () => {
        if (this.isLeader) {
          console.log('👑 Leader tab closing, notifying others');
          this.channel.postMessage({ type: 'leader-gone' });
        }
      });
      
    } catch (error) {
      console.warn('BroadcastChannel not supported, using single-tab mode', error);
      // Fallback: always be leader if BroadcastChannel not supported
      this.isLeader = true;
      if (this.enabled) {
        this.connect();
      }
    }
  }
  
  /**
   * Setup visibility change listener
   */
  setupVisibilityListener() {
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible' && this.enabled && this.isLeader && !this.ws) {
        console.log('👁️ Tab visible, reconnecting...');
        this.attempt = 0;
        this.scheduleReconnect(0);
      }
    });
  }
  
  /**
   * Attempt to become leader tab
   */
  becomeLeader() {
    if (this.isLeader || !this.enabled) return;
    
    console.log('👑 Becoming leader tab');
    this.isLeader = true;
    
    // Send heartbeat to claim leadership
    if (this.channel) {
      this.channel.postMessage({ 
        type: 'leader-heartbeat',
        timestamp: Date.now()
      });
      
      // Send periodic heartbeats
      this.leaderHeartbeatTimer = setInterval(() => {
        if (this.isLeader && this.channel) {
          this.channel.postMessage({ 
            type: 'leader-heartbeat',
            timestamp: Date.now()
          });
        }
      }, 3000);
    }
    
    // Open WebSocket connection
    if (!this.ws && !this.connecting) {
      this.scheduleReconnect(0);
    }
  }
  
  /**
   * Resign from leadership
   */
  resignLeader() {
    if (!this.isLeader) return;
    
    console.log('👑 Resigning from leadership');
    this.isLeader = false;
    
    // Stop heartbeat
    if (this.leaderHeartbeatTimer) {
      clearInterval(this.leaderHeartbeatTimer);
      this.leaderHeartbeatTimer = null;
    }
    
    // Close WebSocket
    this.closeWS();
  }
  
  /**
   * Enable or disable WebSocket connection
   * @param {boolean} value - true to enable, false to disable
   */
  setEnabled(value) {
    if (this.enabled === value) return;
    
    console.log(`📡 WSManager enabled: ${value}`);
    this.enabled = value;
    
    if (!value) {
      // Disable: resign leadership and clean up
      this.resignLeader();
      this.clearTimers();
    } else {
      // Enable: try to become leader
      this.becomeLeader();
    }
  }
  
  /**
   * Subscribe to WebSocket messages
   * @param {Function} callback - Message handler
   * @returns {Function} Unsubscribe function
   */
  subscribe(callback) {
    this.subscribers.add(callback);
    return () => this.subscribers.delete(callback);
  }
  
  /**
   * Notify all subscribers with message
   * @param {*} message - Message to send to subscribers
   */
  notifySubscribers(message) {
    this.subscribers.forEach(callback => {
      try {
        callback(message);
      } catch (error) {
        console.error('Subscriber callback error:', error);
      }
    });
  }
  
  /**
   * Build WebSocket URL with params
   * @returns {string} Full WebSocket URL
   */
  buildURL() {
    const url = new URL(this.config.url);
    Object.entries(this.config.params).forEach(([key, value]) => {
      url.searchParams.set(key, String(value));
    });
    return url.toString();
  }
  
  /**
   * Connect to WebSocket
   */
  connect() {
    // Guards
    if (!this.enabled || !this.isLeader || this.ws || this.connecting) {
      return;
    }
    
    // Don't connect when tab is hidden
    if (document.visibilityState === 'hidden') {
      console.log('📱 Tab hidden, postponing connection');
      this.scheduleReconnect();
      return;
    }
    
    const url = this.buildURL();
    console.log('🔌 Connecting to WebSocket:', url);
    
    this.connecting = true;
    
    try {
      this.ws = new WebSocket(url);
      
      this.ws.onopen = () => {
        console.log('✅ WebSocket connected');
        this.connecting = false;
        this.attempt = 0;
        
        // Start ping heartbeat
        this.pingTimer = setInterval(() => {
          if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            try {
              this.ws.send(JSON.stringify({ type: 'ping', t: Date.now() }));
            } catch (error) {
              console.error('Ping error:', error);
            }
          }
        }, 25000);
        
        // Send initial subscribe message
        try {
          this.ws.send(JSON.stringify({
            type: 'subscribe',
            ...this.config.params
          }));
        } catch (error) {
          console.error('Subscribe error:', error);
        }
      };
      
      this.ws.onmessage = (event) => {
        let payload;
        try {
          payload = JSON.parse(event.data);
        } catch {
          payload = event.data;
        }
        
        // Leader broadcasts to other tabs
        if (this.isLeader && this.channel) {
          try {
            this.channel.postMessage({ 
              type: 'ws-broadcast', 
              payload 
            });
          } catch (error) {
            console.warn('Failed to broadcast message:', error);
          }
        }
        
        // Notify local subscribers
        this.notifySubscribers(payload);
      };
      
      this.ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
      };
      
      this.ws.onclose = (event) => {
        console.log(`🔌 WebSocket closed (code: ${event.code}, reason: ${event.reason || 'none'})`);
        this.connecting = false;
        this.closeWS();
        
        // Reconnect if still enabled and leader
        if (this.enabled && this.isLeader) {
          this.scheduleReconnect();
        }
      };
      
    } catch (error) {
      console.error('❌ Failed to create WebSocket:', error);
      this.connecting = false;
      this.scheduleReconnect();
    }
  }
  
  /**
   * Close WebSocket connection
   */
  closeWS() {
    if (this.ws) {
      try {
        this.ws.close(1000, 'client-close');
      } catch (error) {
        console.warn('Error closing WebSocket:', error);
      }
      this.ws = null;
    }
    
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
  }
  
  /**
   * Clear all timers
   */
  clearTimers() {
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    if (this.leaderHeartbeatTimer) {
      clearInterval(this.leaderHeartbeatTimer);
      this.leaderHeartbeatTimer = null;
    }
  }
  
  /**
   * Schedule reconnection with exponential backoff
   * @param {number} [delay] - Custom delay (optional)
   */
  scheduleReconnect(delay) {
    if (this.reconnectTimer || !this.enabled || !this.isLeader) {
      return;
    }
    
    const attempt = this.attempt++;
    const baseDelay = typeof delay === 'number' 
      ? delay 
      : Math.min(30000, 1000 * Math.pow(2, attempt));
    const jitter = Math.floor(Math.random() * 400);
    const totalDelay = baseDelay + jitter;
    
    console.log(`🔄 Reconnecting in ${(totalDelay / 1000).toFixed(1)}s (attempt ${attempt + 1})`);
    
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, totalDelay);
  }
  
  /**
   * Reset WSManager to initial state
   */
  reset() {
    console.log('🔄 Resetting WSManager');
    this.setEnabled(false);
    this.resignLeader();
    this.clearTimers();
    this.subscribers.clear();
    
    if (this.channel) {
      try {
        this.channel.close();
      } catch (error) {
        console.warn('Error closing BroadcastChannel:', error);
      }
      this.channel = null;
    }
    
    this.created = false;
    this.isLeader = false;
  }
}

// Export singleton instance
export default new WSManager();
