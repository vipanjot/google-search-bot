"""Article routes — list all articles and fetch a single article by filename."""

from fastapi import APIRouter, HTTPException

from backend.config.settings import SCRAPED_DIR
from backend.services.helpers import (
    build_article_summary,
    extract_url,
    parse_frontmatter,
    strip_wikilinks,
)

router = APIRouter()


@router.get("/api/articles")
def list_articles(search: str = "", type: str = ""):
    """
    Return all scraped articles as lightweight summaries.
    Optionally filtered by a search string or article type.
    Sorted newest-first by file modification time.
    """
    if not SCRAPED_DIR.exists():
        return []

    articles = []
    for f in sorted(SCRAPED_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
        # index.md is a generated file, not a real article
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


@router.get("/api/articles/{filename}")
def get_article(filename: str):
    """
    Return the full content of a single article including its parsed body.
    Path-traversal characters are rejected before touching the filesystem.
    """
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(400, "Invalid filename")

    path = SCRAPED_DIR / filename
    if not path.exists():
        raise HTTPException(404, "Article not found")

    content = path.read_text(encoding="utf-8", errors="ignore")
    meta, body = parse_frontmatter(content)
    title = strip_wikilinks(str(meta.get("title", path.stem)))
    # Cast all meta values to safe serialisable types before returning to client
    safe_meta = {k: (v if isinstance(v, (list, dict)) else str(v)) for k, v in meta.items()}

    return {
        "filename": filename,
        "title": title,
        "meta": safe_meta,
        "body": body,
        "url": extract_url(body),
    }
