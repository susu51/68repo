// DEPRECATED - Use /api/http.js instead
// Cookie-based authentication with credentials: 'include'

// HARDCODED FOR DEVELOPMENT - BYPASS .ENV ISSUES  
const BACKEND_URL = 'http://localhost:8001';

console.warn('❌ DEPRECATED: apiClient.js is deprecated. Use /api/http.js with cookie authentication instead.');

// Compatibility wrapper - redirects to cookie-based API
class DeprecatedAPIClient {
  constructor() {
    console.warn('⚠️ APIClient is deprecated. Migrate to cookie-based authentication.');
  }

  setToken(token) {
    console.warn('❌ setToken() is deprecated. Cookies handle authentication automatically.');
  }

  getToken() {
    console.warn('❌ getToken() is deprecated. Use cookie authentication instead.');
    return null;
  }

  isAuthenticated() {
    console.warn('❌ isAuthenticated() is deprecated. Check auth status via /auth/me endpoint.');
    return false;
  }

  async get(endpoint, options = {}) {
    console.warn('❌ apiClient.get() is deprecated. Use /api/http.js get() function instead.');
    throw new Error('Deprecated API client. Use cookie-based http.js');
  }

  async post(endpoint, data = {}, options = {}) {
    console.warn('❌ apiClient.post() is deprecated. Use /api/http.js post() function instead.');
    throw new Error('Deprecated API client. Use cookie-based http.js');
  }

  async put(endpoint, data = {}, options = {}) {
    console.warn('❌ apiClient.put() is deprecated. Use /api/http.js put() function instead.');
    throw new Error('Deprecated API client. Use cookie-based http.js');
  }

  async patch(endpoint, data = {}, options = {}) {
    console.warn('❌ apiClient.patch() is deprecated. Use /api/http.js patch() function instead.');
    throw new Error('Deprecated API client. Use cookie-based http.js');
  }

  async delete(endpoint, options = {}) {
    console.warn('❌ apiClient.delete() is deprecated. Use /api/http.js del() function instead.');
    throw new Error('Deprecated API client. Use cookie-based http.js');
  }
}

// Export deprecated instance for compatibility
export const apiClient = new DeprecatedAPIClient();
export default apiClient;