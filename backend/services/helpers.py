"""
Shared helpers used by multiple route handlers:
  - saved-article persistence (JSON file)
  - markdown frontmatter parsing
  - article summary builder
"""

import json
import re
from pathlib import Path

import yaml

from backend.config.settings import SAVED_FILE, SCRAPED_DIR


# ── Saved-article persistence ─────────────────────────────────────────────────

def load_saved() -> set:
    """Read the saved-articles list from disk; return empty set on any error."""
    if SAVED_FILE.exists():
        try:
            return set(json.loads(SAVED_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
    return set()


def persist_saved(saved: set) -> None:
    """Write the saved-articles set back to disk as sorted JSON."""
    SAVED_FILE.write_text(json.dumps(sorted(saved), indent=2), encoding="utf-8")


# ── Markdown utilities ────────────────────────────────────────────────────────

def strip_wikilinks(text: str) -> str:
    """Remove [[wikilink]] markup so plain text is returned to the client."""
    return re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)


def parse_frontmatter(content: str):
    """
    Split a markdown file into (meta_dict, body_string).
    Files without --- delimiters get an empty meta dict.
    """
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
    """Pull the canonical source URL from the bold Source link in the article body."""
    m = re.search(r"\*\*Source:\*\*\s*\[[^\]]*\]\(([^)]+)\)", body[:800])
    return m.group(1) if m else ""


# ── Article summary builder ───────────────────────────────────────────────────

def build_article_summary(filepath: Path) -> dict:
    """
    Read one .md file and return the lightweight dict used in the article list.
    Full body is excluded here — it's only loaded when a specific article is opened.
    """
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
