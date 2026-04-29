// In dev: Vite proxies /api/* → http://localhost:8000 (vite.config.js)
// In prod: VITE_API_URL is your Cloudflare Tunnel URL, e.g. https://xyz.trycloudflare.com
const BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');

const get = (path) => fetch(`${BASE}${path}`).then(r => r.json());
const del_ = (path) => fetch(`${BASE}${path}`, { method: 'DELETE' }).then(r => r.json());
const post = (path, body) =>
  fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  }).then(r => r.json());

export const fetchArticles = (search = '', type = '') =>
  get(`/api/articles?search=${encodeURIComponent(search)}&type=${encodeURIComponent(type)}`);

export const fetchArticle = (filename) =>
  get(`/api/articles/${encodeURIComponent(filename)}`);

export const fetchSaved = () => get('/api/saved');
export const saveArticle = (filename) => post(`/api/saved/${encodeURIComponent(filename)}`);
export const unsaveArticle = (filename) => del_(`/api/saved/${encodeURIComponent(filename)}`);

export const triggerSearch = (query, num = 20, engine = 'duckduckgo', extra = {}) =>
  post('/api/search', { query, num, engine, ...extra });

export const fetchSearchStatus = () => get('/api/search/status');

export const exportZipUrl = () => `${BASE}/api/export/zip`;
