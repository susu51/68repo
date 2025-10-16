"""
Frontend utility for API-based state management
CI GATE 0 COMPLIANCE - NO localStorage/sessionStorage references
"""

// CSRF token management
let csrfToken = null;

// Get CSRF token from cookie
export const getCsrfToken = () => {
  if (csrfToken) return csrfToken;
  
  const cookies = document.cookie.split(';');
  for (let cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === 'kuryecini_csrf') {
      csrfToken = decodeURIComponent(value);
      return csrfToken;
    }
  }
  return null;
};

// API client with CSRF protection
class SecureApiClient {
  constructor(baseURL = process.env.REACT_APP_API_BASE_URL?.replace('/api', '') || 'https://order-system-44.preview.emergentagent.com') {
    this.baseURL = baseURL;
    this.retryAttempts = 3;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const csrf = getCsrfToken();
    
    const defaultHeaders = {
      'Content-Type': 'application/json',
    };
    
    // Add CSRF token for state-changing operations
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(options.method?.toUpperCase())) {
      if (csrf) {
        defaultHeaders['X-CSRF-Token'] = csrf;
      }
    }
    
    const config = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
      credentials: 'include', // Include cookies
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        if (response.status === 401) {
          // Authentication failed - redirect to login
          window.location.href = '/login';
          return null;
        }
        
        if (response.status === 403) {
          // CSRF error - refresh token and retry
          await this.refreshCSRF();
          return this.request(endpoint, options);
        }
        
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      return data;
      
    } catch (error) {
      console.error(`API Error ${options.method || 'GET'} ${endpoint}:`, error);
      throw error;
    }
  }

  async refreshCSRF() {
    // This would be implemented to refresh the CSRF token
    // For now, just clear the cached token
    csrfToken = null;
  }

  // Convenience methods
  get(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'GET' });
  }

  post(endpoint, data, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  put(endpoint, data, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  patch(endpoint, data, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  delete(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'DELETE' });
  }
}

// Global API client instance
export const apiClient = new SecureApiClient();

// State management utilities (CI GATE 0 COMPLIANT)
export class DatabaseStateManager {
  constructor() {
    this.cache = new Map(); // In-memory cache only
    this.subscribers = new Map();
  }

  // Subscribe to state changes
  subscribe(key, callback) {
    if (!this.subscribers.has(key)) {
      this.subscribers.set(key, new Set());
    }
    this.subscribers.get(key).add(callback);
    
    // Return unsubscribe function
    return () => {
      this.subscribers.get(key)?.delete(callback);
    };
  }

  // Notify subscribers of state changes
  notify(key, data) {
    this.cache.set(key, data);
    const subscribers = this.subscribers.get(key);
    if (subscribers) {
      subscribers.forEach(callback => callback(data));
    }
  }

  // Get cached data
  getCached(key) {
    return this.cache.get(key);
  }

  // Clear cache
  clearCache(key) {
    if (key) {
      this.cache.delete(key);
    } else {
      this.cache.clear();
    }
  }
}

// Global state manager
export const stateManager = new DatabaseStateManager();

// Address Management (API-based)
export class AddressManager {
  static async getAddresses() {
    try {
      const addresses = await apiClient.get('/user/addresses');
      stateManager.notify('addresses', addresses);
      return addresses;
    } catch (error) {
      console.error('Failed to fetch addresses:', error);
      throw error;
    }
  }

  static async addAddress(addressData) {
    try {
      const newAddress = await apiClient.post('/user/addresses', addressData);
      
      // Refresh addresses list
      const updatedAddresses = await this.getAddresses();
      
      return newAddress;
    } catch (error) {
      console.error('Failed to add address:', error);
      throw error;
    }
  }

  static async updateAddress(addressId, updates) {
    try {
      const updatedAddress = await apiClient.patch(`/user/addresses/${addressId}`, updates);
      
      // Refresh addresses list
      await this.getAddresses();
      
      return updatedAddress;
    } catch (error) {
      console.error('Failed to update address:', error);
      throw error;
    }
  }

  static async deleteAddress(addressId) {
    try {
      await apiClient.delete(`/user/addresses/${addressId}`);
      
      // Refresh addresses list
      await this.getAddresses();
      
      return true;
    } catch (error) {
      console.error('Failed to delete address:', error);
      throw error;
    }
  }
}

// Cart Management (API-based)
export class CartManager {
  static async getCart() {
    try {
      const cart = await apiClient.get('/api/cart');
      stateManager.notify('cart', cart);
      return cart;
    } catch (error) {
      console.error('Failed to fetch cart:', error);
      throw error;
    }
  }

  static async updateCart(cartData) {
    try {
      const updatedCart = await apiClient.put('/api/cart', cartData);
      stateManager.notify('cart', updatedCart);
      return updatedCart;
    } catch (error) {
      console.error('Failed to update cart:', error);
      throw error;
    }
  }

  static async addToCart(productId, quantity = 1) {
    try {
      // Get current cart
      let cart = stateManager.getCached('cart');
      if (!cart) {
        cart = await this.getCart();
      }

      // Find existing item or add new one
      const existingItemIndex = cart.items.findIndex(item => item.product_id === productId);
      
      if (existingItemIndex >= 0) {
        cart.items[existingItemIndex].qty += quantity;
      } else {
        cart.items.push({
          product_id: productId,
          qty: quantity
        });
      }

      return await this.updateCart({ items: cart.items });
    } catch (error) {
      console.error('Failed to add to cart:', error);
      throw error;
    }
  }

  static async removeFromCart(productId) {
    try {
      let cart = stateManager.getCached('cart');
      if (!cart) {
        cart = await this.getCart();
      }

      cart.items = cart.items.filter(item => item.product_id !== productId);
      return await this.updateCart({ items: cart.items });
    } catch (error) {
      console.error('Failed to remove from cart:', error);
      throw error;
    }
  }

  static async updateQuantity(productId, quantity) {
    try {
      if (quantity <= 0) {
        return await this.removeFromCart(productId);
      }

      let cart = stateManager.getCached('cart');
      if (!cart) {
        cart = await this.getCart();
      }

      const itemIndex = cart.items.findIndex(item => item.product_id === productId);
      if (itemIndex >= 0) {
        cart.items[itemIndex].qty = quantity;
        return await this.updateCart({ items: cart.items });
      }

      return cart;
    } catch (error) {
      console.error('Failed to update cart quantity:', error);
      throw error;
    }
  }

  static async clearCart() {
    try {
      return await this.updateCart({ items: [] });
    } catch (error) {
      console.error('Failed to clear cart:', error);
      throw error;
    }
  }
}

// Preferences Management (API-based)
export class PreferencesManager {
  static async getPreferences() {
    try {
      const preferences = await apiClient.get('/api/preferences');
      stateManager.notify('preferences', preferences);
      return preferences;
    } catch (error) {
      console.error('Failed to fetch preferences:', error);
      throw error;
    }
  }

  static async updatePreferences(updates) {
    try {
      const updatedPreferences = await apiClient.put('/api/preferences', updates);
      stateManager.notify('preferences', updatedPreferences);
      return updatedPreferences;
    } catch (error) {
      console.error('Failed to update preferences:', error);
      throw error;
    }
  }
}

// Loyalty Points Management
export class LoyaltyManager {
  static async getPoints() {
    try {
      const loyaltyData = await apiClient.get('/api/loyalty/points');
      stateManager.notify('loyalty', loyaltyData);
      return loyaltyData;
    } catch (error) {
      console.error('Failed to fetch loyalty points:', error);
      throw error;
    }
  }

  static async spendPoints(points, description) {
    try {
      const result = await apiClient.post('/api/loyalty/consume', {
        points,
        description
      });
      
      // Refresh loyalty data
      await this.getPoints();
      
      return result;
    } catch (error) {
      console.error('Failed to spend loyalty points:', error);
      throw error;
    }
  }
}

// CI GATE 0 COMPLIANCE - Migration utilities removed
// All data management is API-based only

// CI GATE 0 COMPLIANCE - No localStorage override utilities needed

// Toast utility for API errors
export const showApiError = (error, defaultMessage = 'Bir hata oluştu') => {
  let message = defaultMessage;
  
  if (error?.message) {
    message = error.message;
  } else if (typeof error === 'string') {
    message = error;
  }
  
  // Use your existing toast system
  if (window.toast) {
    window.toast.error(message);
  } else {
    console.error('API Error:', message);
  }
};

// CI GATE 0 COMPLIANCE - All client-side storage is API-based only