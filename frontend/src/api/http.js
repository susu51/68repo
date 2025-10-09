// HTTP client utility with HttpOnly cookie support
// NO localStorage - ALL auth via cookies

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export const api = async (path, init = {}) => {
  const url = `${API_BASE_URL}/api${path}`;
  
  const config = {
    credentials: "include", // CRITICAL: Send cookies
    headers: { 
      "Content-Type": "application/json", 
      ...(init.headers || {}) 
    },
    ...init,
  };

  try {
    const res = await fetch(url, config);
    
    if (!res.ok) {
      // Handle auth errors
      if (res.status === 401) {
        // Only try refresh if we're not already on an auth endpoint
        if (!path.includes('/auth/')) {
          try {
            await refreshAuth();
            // Retry original request
            const retryRes = await fetch(url, config);
            if (!retryRes.ok) {
              throw new Error(`${retryRes.status} ${retryRes.statusText}`);
            }
            return retryRes;
          } catch (refreshError) {
            // Refresh failed, just throw error without redirecting
            throw new Error('Authentication expired');
          }
        } else {
          // For auth endpoints, just throw the error without trying to refresh
          throw new Error(`${res.status} ${res.statusText}`);
        }
      }
      throw new Error(`${res.status} ${res.statusText}`);
    }
    
    return res;
  } catch (error) {
    console.error(`API Error [${init.method || 'GET'} ${path}]:`, error);
    throw error;
  }
};

// Refresh token helper
const refreshAuth = async () => {
  const res = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
    method: 'POST',
    credentials: 'include'
  });
  
  if (!res.ok) {
    throw new Error('Refresh failed');
  }
  
  return res;
};

// Convenience methods
export const get = (path, options = {}) => api(path, { method: 'GET', ...options });
export const post = (path, body, options = {}) => api(path, { 
  method: 'POST', 
  body: JSON.stringify(body),
  ...options 
});
export const put = (path, body, options = {}) => api(path, { 
  method: 'PUT', 
  body: JSON.stringify(body),
  ...options 
});
export const patch = (path, body, options = {}) => api(path, { 
  method: 'PATCH', 
  body: JSON.stringify(body),
  ...options 
});
export const del = (path, options = {}) => api(path, { method: 'DELETE', ...options });

export default api;