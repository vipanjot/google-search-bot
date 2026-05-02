// In dev: Vite proxies /api/* → http://localhost:8000 (vite.config.js)
// In prod: URL and API key are read from localStorage (set via Settings panel)
const LS_KEY = 'searchbot_api_url';
const LS_KEY_SECRET = 'searchbot_api_secret';

export const getApiUrl = () =>
  (localStorage.getItem(LS_KEY) || import.meta.env.VITE_API_URL || '').replace(/\/$/, '');

export const setApiUrl = (url) => {
  const clean = (url || '').trim().replace(/\/$/, '');
  if (clean) localStorage.setItem(LS_KEY, clean);
  else localStorage.removeItem(LS_KEY);
};

export const getApiSecret = () => localStorage.getItem(LS_KEY_SECRET) || '';

export const setApiSecret = (secret) => {
  const clean = (secret || '').trim();
  if (clean) localStorage.setItem(LS_KEY_SECRET, clean);
  else localStorage.removeItem(LS_KEY_SECRET);
};

const authHeaders = (extra = {}) => ({
  ...extra,
  'X-API-Key': getApiSecret(),
});

const get = (path) =>
  fetch(`${getApiUrl()}${path}`, { headers: authHeaders() }).then(r => r.json());
const del_ = (path) =>
  fetch(`${getApiUrl()}${path}`, { method: 'DELETE', headers: authHeaders() }).then(r => r.json());
const post = (path, body) =>
  fetch(`${getApiUrl()}${path}`, {
    method: 'POST',
    headers: authHeaders(body ? { 'Content-Type': 'application/json' } : {}),
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
