import { useState, useEffect } from 'react';
import { getApiUrl, setApiUrl, getApiSecret, setApiSecret } from '../services/client';

export default function SettingsPanel({ open, onClose }) {
  const [url, setUrl] = useState('');
  const [secret, setSecret] = useState('');
  const [status, setStatus] = useState(null); // null | 'ok' | 'error'
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    if (open) {
      setUrl(getApiUrl());
      setSecret(getApiSecret());
      setStatus(null);
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  const testConnection = async () => {
    const base = url.trim().replace(/\/$/, '');
    if (!base) { setStatus('error'); return; }
    setTesting(true);
    setStatus(null);
    try {
      const r = await fetch(`${base}/api/articles?search=&type=`, {
        headers: { 'X-API-Key': secret.trim() },
        signal: AbortSignal.timeout(5000),
      });
      setStatus(r.ok ? 'ok' : 'error');
    } catch {
      setStatus('error');
    } finally {
      setTesting(false);
    }
  };

  const handleSave = () => {
    setApiUrl(url);
    setApiSecret(secret);
    onClose();
  };

  if (!open) return null;

  return (
    <div className="modal-overlay active" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-container settings-panel" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-header-meta">
            <span className="settings-heading">Settings</span>
          </div>
          <div className="modal-header-actions">
            <button className="modal-close" onClick={onClose} aria-label="Close">✕</button>
          </div>
        </div>

        <div className="settings-body">
          <p className="settings-label">Backend API URL</p>
          <p className="settings-hint">
            Paste your Cloudflare Tunnel URL (e.g.{' '}
            <code>https://xyz.trycloudflare.com</code>). Saved in your browser —
            no redeploy needed when the tunnel URL changes.
          </p>

          <div className="settings-input-row">
            <input
              className="settings-input"
              type="url"
              placeholder="https://xyz.trycloudflare.com"
              value={url}
              onChange={e => { setUrl(e.target.value); setStatus(null); }}
              onKeyDown={e => e.key === 'Enter' && testConnection()}
              spellCheck={false}
            />
            <button
              className="settings-test-btn"
              onClick={testConnection}
              disabled={testing || !url.trim()}
            >
              {testing ? <span className="spinner-small" /> : 'Test'}
            </button>
          </div>

          <p className="settings-label" style={{ marginTop: '1rem' }}>API Secret Key</p>
          <p className="settings-hint">
            The <code>API_SECRET</code> value from your backend <code>.env</code> file.
            Sent as <code>X-API-Key</code> with every request.
          </p>
          <input
            className="settings-input"
            type="password"
            placeholder="your-secret-token"
            value={secret}
            onChange={e => { setSecret(e.target.value); setStatus(null); }}
            spellCheck={false}
          />

          {status === 'ok' && (
            <p className="settings-status ok">Connected successfully</p>
          )}
          {status === 'error' && (
            <p className="settings-status error">
              Could not connect — check the URL, tunnel, and API secret key.
            </p>
          )}

          <div className="settings-actions">
            <button className="settings-clear-btn" onClick={() => { setUrl(''); setSecret(''); setStatus(null); }}>
              Clear
            </button>
            <button className="settings-save-btn" onClick={handleSave}>
              Save & Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
