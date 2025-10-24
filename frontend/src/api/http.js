// HTTP client utility with double /api prevention and cookie mandatory
const BASE = (process.env.REACT_APP_API_BASE_URL || process.env.REACT_APP_BACKEND_URL + '/api').replace(/\/+$/, ''); // remove trailing /

const sanitizePath = (p) => {
  // always start with single /
  let path = ('/' + (p || '')).replace(/\/+/g, '/');
  // BASE already ends with /api → trim leading /api
  path = path.replace(/^\/api(\/|$)/, '/');
  return path;
};

export async function api(path, init = {}) {
  const url = BASE + sanitizePath(path);
  const res = await fetch(url, {
    credentials: 'include',                          // COOKIE MANDATORY
    headers: { 'Content-Type': 'application/json', ...(init.headers || {}) },
    ...init
  });
  
  // Don't throw generic "Authentication expired" for all 401s
  // Let the caller handle the specific error message from backend
  if (!res.ok && res.status !== 401) {
    throw new Error(`${res.status} ${res.statusText}`);
  }
  
  return res;
}

export const get = async (p) => {
  const res = await api(p);
  
  // Handle non-OK responses (including 401)
  if (!res.ok) {
    // Try to parse error message from response
    let errorMessage = `HTTP ${res.status}`;
    try {
      const errorData = await res.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch {
      // Response body is not JSON or empty
    }
    throw new Error(errorMessage);
  }
  
  const data = await res.json();
  return { data };
};

export const post = async (p, b) => {
  const res = await api(p, { method: 'POST', body: JSON.stringify(b) });
  
  // Handle non-OK responses
  if (!res.ok) {
    let errorMessage = `HTTP ${res.status}`;
    try {
      const errorData = await res.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch {
      errorMessage = res.statusText || errorMessage;
    }
    throw new Error(errorMessage);
  }
  
  const data = await res.json();
  return { data };
};

export const patch = async (p, b) => {
  const res = await api(p, { method: 'PATCH', body: JSON.stringify(b) });
  
  // Handle non-OK responses
  if (!res.ok) {
    let errorMessage = `HTTP ${res.status}`;
    try {
      const errorData = await res.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch {
      errorMessage = res.statusText || errorMessage;
    }
    throw new Error(errorMessage);
  }
  
  const data = await res.json();
  return { data };
};

export const del = async (p) => {
  const res = await api(p, { method: 'DELETE' });
  
  // Handle non-OK responses
  if (!res.ok) {
    let errorMessage = `HTTP ${res.status}`;
    try {
      const errorData = await res.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch {
      errorMessage = res.statusText || errorMessage;
    }
    throw new Error(errorMessage);
  }
  
  // DELETE may not return JSON body
  try {
    const data = await res.json();
    return { data };
  } catch {
    return { data: null };
  }
};

// Legacy compatibility exports  
// Note: Named exports (get, post, patch, del) now all return { data } format
export default {
  async get(path) {
    // get() already returns { data }, use it directly
    return await get(path);
  },
  async post(path, body) {
    // post() now returns { data } or throws error
    return await post(path, body);
  },
  async patch(path, body) {
    // patch() now returns { data } or throws error
    return await patch(path, body);
  },
  async delete(path) {
    // del() now returns { data } or throws error
    return await del(path);
  }
};