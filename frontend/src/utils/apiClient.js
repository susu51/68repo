import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
export const API_BASE = `${BACKEND_URL}/api`;

// API client utility with auth token management
class APIClient {
  constructor() {
    this.token = null;
  }

  // Set token (called by AuthContext)
  setToken(token) {
    this.token = token;
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }

  // Get token (no localStorage fallback)
  getToken() {
    return this.token;
  }

  // Get auth headers
  getAuthHeaders() {
    if (!this.token) {
      throw new Error('Authentication token not available. Please login.');
    }
    return {
      'Authorization': `Bearer ${this.token}`,
      'Content-Type': 'application/json'
    };
  }

  // Check if authenticated
  isAuthenticated() {
    return !!this.token;
  }

  // Generic API calls with automatic auth headers
  async get(endpoint, options = {}) {
    try {
      const headers = this.isAuthenticated() ? this.getAuthHeaders() : {};
      const response = await axios.get(`${API_BASE}${endpoint}`, {
        ...options,
        headers: { ...headers, ...options.headers }
      });
      return response.data;
    } catch (error) {
      if (error.response?.status === 401) {
        throw new Error('Session expired. Please login again.');
      }
      throw error;
    }
  }

  async post(endpoint, data = {}, options = {}) {
    try {
      const headers = this.isAuthenticated() ? this.getAuthHeaders() : {};
      const response = await axios.post(`${API_BASE}${endpoint}`, data, {
        ...options,
        headers: { ...headers, ...options.headers }
      });
      return response.data;
    } catch (error) {
      if (error.response?.status === 401) {
        throw new Error('Session expired. Please login again.');
      }
      throw error;
    }
  }

  async patch(endpoint, data = {}, options = {}) {
    try {
      const headers = this.isAuthenticated() ? this.getAuthHeaders() : {};
      const response = await axios.patch(`${API_BASE}${endpoint}`, data, {
        ...options,
        headers: { ...headers, ...options.headers }
      });
      return response;
    } catch (error) {
      if (error.response?.status === 401) {
        throw new Error('Session expired. Please login again.');
      }
      throw error;
    }
  }

  async put(endpoint, data = {}, options = {}) {
    try {
      const headers = this.isAuthenticated() ? this.getAuthHeaders() : {};
      const response = await axios.put(`${API_BASE}${endpoint}`, data, {
        ...options,
        headers: { ...headers, ...options.headers }
      });
      return response;
    } catch (error) {
      if (error.response?.status === 401) {
        throw new Error('Session expired. Please login again.');
      }
      throw error;
    }
  }

  async delete(endpoint, options = {}) {
    try {
      const headers = this.isAuthenticated() ? this.getAuthHeaders() : {};
      const response = await axios.delete(`${API_BASE}${endpoint}`, {
        ...options,
        headers: { ...headers, ...options.headers }
      });
      return response;
    } catch (error) {
      if (error.response?.status === 401) {
        throw new Error('Session expired. Please login again.');
      }
      throw error;
    }
  }
}

// Export singleton instance
export const apiClient = new APIClient();
export default apiClient;