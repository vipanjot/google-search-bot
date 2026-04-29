#!/usr/bin/env python
"""FastAPI backend for the Search Bot UI."""

import io
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import yaml
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Search Bot API")

# Allow all origins — personal tool accessed via Cloudflare tunnel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

SCRAPED_DIR = Path("scraped-articles")
SAVED_FILE = Path("saved_articles.json")

_search_status: dict = {"running": False, "message": "", "query": ""}


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_saved() -> set:
    if SAVED_FILE.exists():
        try:
            return set(json.loads(SAVED_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
    return set()


def persist_saved(saved: set) -> None:
    SAVED_FILE.write_text(json.dumps(sorted(saved), indent=2), encoding="utf-8")


def strip_wikilinks(text: str) -> str:
    return re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)


def parse_frontmatter(content: str):
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    try:
        meta = yaml.safe_load(parts[1]) or {}
    except Exception:
        meta = {}
    return meta, parts[2].strip()


def extract_url(body: str) -> str:
    m = re.search(r"\*\*Source:\*\*\s*\[[^\]]*\]\(([^)]+)\)", body[:800])
    return m.group(1) if m else ""


def build_article_summary(filepath: Path) -> dict:
    content = filepath.read_text(encoding="utf-8", errors="ignore")
    meta, body = parse_frontmatter(content)
    title = strip_wikilinks(str(meta.get("title", filepath.stem)))
    summary = strip_wikilinks(str(meta.get("summary", ""))[:300])
    tags = meta.get("tags", []) or []
    tags = [str(t) for t in (tags if isinstance(tags, list) else [])][:8]
    return {
        "filename": filepath.name,
        "title": title,
        "summary": summary,
        "tags": tags,
        "type": str(meta.get("type", "concept")),
        "date_created": str(meta.get("date_created", "")),
        "status": str(meta.get("status", "draft")),
        "url": extract_url(body),
    }


def _auto_git_commit(query: str) -> None:
    """Commit newly scraped articles to the local git repo (if one exists)."""
    if not Path(".git").exists():
        return
    try:
        subprocess.run(
            ["git", "add", "scraped-articles/", "saved_articles.json"],
            capture_output=True, cwd=str(Path.cwd())
        )
        result = subprocess.run(
            ["git", "commit", "-m", f"scrape: {query}"],
            capture_output=True, text=True, cwd=str(Path.cwd())
        )
        # Auto-push if remote is configured and AUTO_GIT_PUSH=true
        if os.environ.get("AUTO_GIT_PUSH", "").lower() == "true" and result.returncode == 0:
            subprocess.run(
                ["git", "push"],
                capture_output=True, cwd=str(Path.cwd())
            )
    except Exception:
        pass


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/api/articles")
def list_articles(search: str = "", type: str = ""):
    if not SCRAPED_DIR.exists():
        return []
    articles = []
    for f in sorted(SCRAPED_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
        if f.name == "index.md":
            continue
        try:
            articles.append(build_article_summary(f))
        except Exception:
            continue

    if search:
        q = search.lower()
        articles = [
            a for a in articles
            if q in a["title"].lower()
            or q in a["summary"].lower()
            or any(q in t.lower() for t in a["tags"])
        ]
    if type:
        articles = [a for a in articles if a["type"] == type]

    return articles


@app.get("/api/articles/{filename}")
def get_article(filename: str):
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(400, "Invalid filename")
    path = SCRAPED_DIR / filename
    if not path.exists():
        raise HTTPException(404, "Article not found")
    content = path.read_text(encoding="utf-8", errors="ignore")
    meta, body = parse_frontmatter(content)
    title = strip_wikilinks(str(meta.get("title", path.stem)))
    safe_meta = {k: (v if isinstance(v, (list, dict)) else str(v)) for k, v in meta.items()}
    return {
        "filename": filename,
        "title": title,
        "meta": safe_meta,
        "body": body,
        "url": extract_url(body),
    }


@app.get("/api/saved")
def get_saved():
    return sorted(load_saved())


@app.post("/api/saved/{filename}")
def save_article(filename: str):
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(400, "Invalid filename")
    saved = load_saved()
    saved.add(filename)
    persist_saved(saved)
    return {"saved": sorted(saved)}


@app.delete("/api/saved/{filename}")
def unsave_article(filename: str):
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(400, "Invalid filename")
    saved = load_saved()
    saved.discard(filename)
    persist_saved(saved)
    return {"saved": sorted(saved)}


@app.get("/api/export/zip")
def export_zip():
    """Download all scraped articles as a ZIP file."""
    buf = io.BytesIO()
    count = 0
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        if SCRAPED_DIR.exists():
            for f in sorted(SCRAPED_DIR.glob("*.md")):
                zf.write(f, f"scraped-articles/{f.name}")
                count += 1
        if SAVED_FILE.exists():
            zf.write(SAVED_FILE, "saved_articles.json")
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="searchbot-articles.zip"'},
    )


class SearchRequest(BaseModel):
    query: str
    num: int = 20
    engine: str = "duckduckgo"
    output_dir: str = "scraped-articles"
    google_api_key: str = ""
    google_cx: str = ""


def _run_bot(req: SearchRequest) -> None:
    global _search_status
    _search_status.update({"running": True, "message": f'Searching: "{req.query}"', "query": req.query})
    cmd = [
        sys.executable, "bot.py", req.query,
        "-n", str(req.num),
        "-o", req.output_dir,
        "--engine", req.engine,
    ]
    if req.engine == "google":
        cmd += ["--google-api-key", req.google_api_key, "--google-cx", req.google_cx]
    try:
        subprocess.run(cmd, capture_output=True, text=True, cwd=str(Path.cwd()), timeout=300)
        _search_status["message"] = f'Saved to PC: "{req.query}"'
        _auto_git_commit(req.query)
    except subprocess.TimeoutExpired:
        _search_status["message"] = "Search timed out"
    except Exception as exc:
        _search_status["message"] = f"Error: {exc}"
    finally:
        _search_status["running"] = False


@app.post("/api/search")
def trigger_search(req: SearchRequest, bg: BackgroundTasks):
    if _search_status["running"]:
        raise HTTPException(409, "Search already running")
    bg.add_task(_run_bot, req)
    return {"status": "started", "query": req.query}


@app.get("/api/search/status")
def search_status():
    return _search_status


# Serve built frontend in production
_frontend_dist = Path("frontend/dist")
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="static")
