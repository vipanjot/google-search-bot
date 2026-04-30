# Work Log

> One entry per session. Append new entries at the bottom — never edit past ones.
> Format: `### [YYYY-MM-DD] — Session Title`

---

### [2026-04-29] — SettingsPanel Wiring + Cloudflare Tunnel Guide

**Completed:**
- Wired `SettingsPanel` into `App.jsx` — was imported but never rendered or connected
  - Added `settingsOpen` state via `useState(false)`
  - Passed `onOpenSettings` callback to `<Navbar>` so the ⚙ button opens the panel
  - Rendered `<SettingsPanel open={settingsOpen} onClose={...} />` in the JSX
- Explained Cloudflare Tunnel setup (quick tunnel via `cloudflared` + named tunnel option)

**Decisions:**
- Firebase Auth skipped for now — deferred by owner
- Backend stays as Python + FastAPI (not migrating to Node.js + Express)
- Cloudflare Tunnel URL is saved in `localStorage` via the Settings panel — no redeploy needed when tunnel URL changes

**Files Changed:**
- `frontend/src/App.jsx`

**Next Steps:**
- Set up Cloudflare Tunnel to expose local FastAPI backend
- Fill in project name/description in `Claude.txt`

---

### [2026-04-29] — Full Project Restructure (Claude.txt compliance)

**Completed:**

**Frontend:**
- Renamed `src/api/` → `src/services/` — updated imports in all 9 affected files
- Renamed `src/store/` → `src/context/` — updated imports in all 9 affected files
- Created `src/pages/`, `src/hooks/`, `src/utils/` (with `.gitkeep` placeholders)

**Backend:**
- Split monolithic `api.py` into `backend/` package:
  - `backend/config/settings.py` — all paths and env-driven config
  - `backend/models/schemas.py` — Pydantic request models
  - `backend/services/helpers.py` — load_saved, persist_saved, article parsing
  - `backend/services/bot.py` — web scraper (moved from root `bot.py`)
  - `backend/routes/articles.py` — GET /api/articles + GET /api/articles/{filename}
  - `backend/routes/saved.py` — GET/POST/DELETE /api/saved
  - `backend/routes/search.py` — POST /api/search + GET /api/search/status
  - `backend/routes/export.py` — GET /api/export/zip
  - `backend/main.py` — FastAPI app + CORS + router registration
- Root `api.py` reduced to a thin shim so `uvicorn api:app` still works
- Deleted root `bot.py` (now lives at `backend/services/bot.py`)

**Config:**
- Created `.env.example` with all supported environment variables and placeholder values

**Decisions:**
- Firebase Auth deferred — excluded by owner
- Backend stays FastAPI/Python (not migrating to Node.js/Express)
- CORS stays `*` — personal tool via Cloudflare Tunnel only

**Files Changed:**
- `api.py`, all `frontend/src/**` files, new `backend/` package

---

### [2026-04-29] — Cloudflare Tunnel Setup

**Completed:**
- Confirmed `cloudflared-windows-amd64.exe` already present in project root
- Documented full quick-tunnel workflow:
  1. Start backend: `uvicorn api:app --host 127.0.0.1 --port 8000`
  2. Start tunnel: `.\cloudflared-windows-amd64.exe tunnel --url http://localhost:8000`
  3. Copy the generated `https://*.trycloudflare.com` URL
  4. Paste into app Settings panel (⚙ → Backend API URL → Test → Save & Close)
- URL is persisted in `localStorage` — survives page refresh, just needs updating when tunnel restarts

**Decisions:**
- Using quick tunnels (no login, no named tunnel) — URL changes each session, low risk for personal tool
- Named tunnel with stable URL + access controls deferred (can add later if needed)

**Files Changed:**
- None (setup is runtime-only)
