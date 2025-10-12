// HTTP client utility with double /api prevention and cookie mandatory
const BASE = (process.env.REACT_APP_API_BASE_URL || 'https://kurye-express-2.preview.emergentagent.com/api').replace(/\/+$/, ''); // remove trailing /

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
  if (res.status === 401) throw new Error('Authentication expired');
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res;
}

export const get = (p) => api(p);
export const post = (p, b) => api(p, { method: 'POST', body: JSON.stringify(b) });
export const patch = (p, b) => api(p, { method: 'PATCH', body: JSON.stringify(b) });
export const del = (p) => api(p, { method: 'DELETE' });

// Legacy compatibility exports
export default {
  async get(path) {
    const res = await get(path);
    const data = await res.json();
    return { data };
  },
  async post(path, body) {
    const res = await post(path, body);
    const data = await res.json();
    return { data };
  },
  async patch(path, body) {
    const res = await patch(path, body);
    const data = await res.json();
    return { data };
  },
  async delete(path) {
    const res = await del(path);
    const data = await res.json();
    return { data };
  }
};