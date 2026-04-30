// In dev: Vite proxies /api/* → http://localhost:8000 (vite.config.js)
// In prod: URL is read from localStorage (set via Settings panel), falling back to VITE_API_URL
const LS_KEY = 'searchbot_api_url';

export const getApiUrl = () =>
  (localStorage.getItem(LS_KEY) || import.meta.env.VITE_API_URL || '').replace(/\/$/, '');

export const setApiUrl = (url) => {
  const clean = (url || '').trim().replace(/\/$/, '');
  if (clean) localStorage.setItem(LS_KEY, clean);
  else localStorage.removeItem(LS_KEY);
};

const get = (path) => fetch(`${getApiUrl()}${path}`).then(r => r.json());
const del_ = (path) => fetch(`${getApiUrl()}${path}`, { method: 'DELETE' }).then(r => r.json());
const post = (path, body) =>
  fetch(`${getApiUrl()}${path}`, {
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

export const exportZipUrl = () => `${getApiUrl()}/api/export/zip`;
