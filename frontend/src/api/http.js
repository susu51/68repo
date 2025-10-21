// HTTP client utility with double /api prevention and cookie mandatory
const BASE = (process.env.REACT_APP_API_BASE_URL || 'https://ai-order-debug.preview.emergentagent.com/api').replace(/\/+$/, ''); // remove trailing /

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
  const data = await res.json();
  return { data };
};
export const post = (p, b) => api(p, { method: 'POST', body: JSON.stringify(b) });
export const patch = (p, b) => api(p, { method: 'PATCH', body: JSON.stringify(b) });
export const del = (p) => api(p, { method: 'DELETE' });

// Legacy compatibility exports
// Note: Named exports (get, post, patch, del) already return parsed data
export default {
  async get(path) {
    // get() already returns { data: parsed }, no need to parse again
    return await get(path);
  },
  async post(path, body) {
    // post() returns Response object, need to parse
    const res = await post(path, body);
    const data = await res.json();
    return { data };
  },
  async patch(path, body) {
    // patch() returns Response object, need to parse
    const res = await patch(path, body);
    const data = await res.json();
    return { data };
  },
  async delete(path) {
    // del() returns Response object, need to parse
    const res = await del(path);
    const data = await res.json();
    return { data };
  }
};