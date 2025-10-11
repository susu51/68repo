// HTTP client utility with HttpOnly cookie support
// NO localStorage - ALL auth via cookies

// Get backend URL from environment variable
const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || window.location.origin;

export const api = async (path, init = {}) => {
  const url = `${API_BASE_URL}/api${path}`;
  
  // CI GATE 0 COMPLIANCE - NO localStorage usage
  // ALL auth via HttpOnly cookies only
  
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
      // Try to get error details from response body
      let errorMessage = `${res.status} ${res.statusText}`;
      try {
        const errorData = await res.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch (e) {
        // If parsing fails, use default message
      }
      
      // Handle auth errors
      if (res.status === 401) {
        // Only try refresh if we're not already on an auth endpoint
        if (!path.includes('/auth/')) {
          try {
            await refreshAuth();
            // Retry original request
            const retryRes = await fetch(url, config);
            if (!retryRes.ok) {
              const retryError = await retryRes.json().catch(() => ({}));
              throw new Error(retryError.detail || retryError.message || `${retryRes.status} ${retryRes.statusText}`);
            }
            return retryRes;
          } catch (refreshError) {
            // Refresh failed, just throw error without redirecting
            throw new Error('Authentication expired');
          }
        }
      }
      
      // For other errors, throw with detailed message
      throw new Error(errorMessage);
    }
    
    return res;
  } catch (error) {
    console.error(`API Error [${init.method || 'GET'} ${path}]:`, error);
    throw error;
  }
};

// Refresh token helper
const refreshAuth = async () => {
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || window.location.origin;
  const res = await fetch(`${BACKEND_URL}/api/auth/refresh`, {
    method: 'POST',
    credentials: 'include'
  });
  
  if (!res.ok) {
    throw new Error('Refresh failed');
  }
  
  return res;
};

// Convenience methods that return parsed JSON with .data wrapper for compatibility
export const get = async (path, options = {}) => {
  const res = await api(path, { method: 'GET', ...options });
  const data = await res.json();
  return { data };
};

export const post = async (path, body, options = {}) => {
  const res = await api(path, { 
    method: 'POST', 
    body: JSON.stringify(body),
    ...options 
  });
  const data = await res.json();
  return { data };
};

export const put = async (path, body, options = {}) => {
  const res = await api(path, { 
    method: 'PUT', 
    body: JSON.stringify(body),
    ...options 
  });
  const data = await res.json();
  return { data };
};

export const patch = async (path, body, options = {}) => {
  const res = await api(path, { 
    method: 'PATCH', 
    body: JSON.stringify(body),
    ...options 
  });
  const data = await res.json();
  return { data };
};

export const del = async (path, options = {}) => {
  const res = await api(path, { method: 'DELETE', ...options });
  const data = await res.json();
  return { data };
};

export default api;