"""
Search routes — trigger a bot scrape run and poll its status.
The bot runs as a subprocess so it can be killed/timed-out independently
and so its stdout/stderr don't block the API event loop.
"""

import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException

from backend.config.settings import AUTO_GIT_PUSH, BOT_SCRIPT, BOT_TIMEOUT
from backend.models.schemas import SearchRequest

router = APIRouter()

# In-process status dict — single-worker assumption (personal tool, not multi-process)
_search_status: dict = {"running": False, "message": "", "query": ""}


def _auto_git_commit(query: str) -> None:
    """
    Commit newly scraped articles after a successful run.
    Only fires when a .git directory exists and AUTO_GIT_PUSH=true is set.
    """
    if not Path(".git").exists():
        return
    try:
        subprocess.run(
            ["git", "add", "scraped-articles/", "saved_articles.json"],
            capture_output=True,
            cwd=str(Path.cwd()),
        )
        result = subprocess.run(
            ["git", "commit", "-m", f"scrape: {query}"],
            capture_output=True,
            text=True,
            cwd=str(Path.cwd()),
        )
        if AUTO_GIT_PUSH and result.returncode == 0:
            subprocess.run(["git", "push"], capture_output=True, cwd=str(Path.cwd()))
    except Exception:
        pass


def _run_bot(req: SearchRequest) -> None:
    """
    Background task: invoke bot.py as a subprocess, update the shared status dict,
    then auto-commit if the run succeeds.
    """
    global _search_status
    _search_status.update({"running": True, "message": f'Searching: "{req.query}"', "query": req.query})

    cmd = [
        sys.executable, str(BOT_SCRIPT), req.query,
        "-n", str(req.num),
        "-o", req.output_dir,
        "--engine", req.engine,
    ]
    if req.engine == "google":
        cmd += ["--google-api-key", req.google_api_key, "--google-cx", req.google_cx]

    try:
        subprocess.run(cmd, capture_output=True, text=True, cwd=str(Path.cwd()), timeout=BOT_TIMEOUT)
        _search_status["message"] = f'Saved to PC: "{req.query}"'
        _auto_git_commit(req.query)
    except subprocess.TimeoutExpired:
        _search_status["message"] = "Search timed out"
    except Exception as exc:
        _search_status["message"] = f"Error: {exc}"
    finally:
        _search_status["running"] = False


@router.post("/api/search")
def trigger_search(req: SearchRequest, bg: BackgroundTasks):
    """
    Start a bot scrape run in the background.
    Rejects the request with 409 if a run is already in progress.
    """
    if _search_status["running"]:
        raise HTTPException(409, "Search already running")
    bg.add_task(_run_bot, req)
    return {"status": "started", "query": req.query}


@router.get("/api/search/status")
def search_status():
    """Return the current bot run status for the frontend to poll."""
    return _search_status
