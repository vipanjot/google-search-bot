"""Saved-articles routes — read, add, and remove bookmarked articles."""

from fastapi import APIRouter, HTTPException

from backend.services.helpers import load_saved, persist_saved

router = APIRouter()


@router.get("/api/saved")
def get_saved():
    """Return the sorted list of saved article filenames."""
    return sorted(load_saved())


@router.post("/api/saved/{filename}")
def save_article(filename: str):
    """
    Add an article to the saved list.
    Path-traversal characters are rejected so callers cannot escape SCRAPED_DIR.
    """
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(400, "Invalid filename")
    saved = load_saved()
    saved.add(filename)
    persist_saved(saved)
    return {"saved": sorted(saved)}


@router.delete("/api/saved/{filename}")
def unsave_article(filename: str):
    """Remove an article from the saved list."""
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(400, "Invalid filename")
    saved = load_saved()
    saved.discard(filename)
    persist_saved(saved)
    return {"saved": sorted(saved)}
