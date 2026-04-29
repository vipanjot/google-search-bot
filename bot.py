#!/usr/bin/env python
"""
Web Search Bot
Searches the web (DuckDuckGo by default, or Google Custom Search JSON API),
visits each result page, and saves structured Markdown files with:
  - YAML frontmatter (title, date, summary, tags, type, status)
  - Bold key terms on first use per article
  - [[wikilinks]] for cross-references (first occurrence per section)
  - kebab-case filenames / {author}-{year}-{title}.md for sources

Usage:
    python bot.py "your search query"
    python bot.py "machine learning" -n 50 -o ./my-articles --delay 3
    python bot.py "climate change" --engine google --google-api-key KEY --google-cx CX_ID
"""

import re
import sys
import time
import json
import yaml
import argparse
import requests
import html2text
from datetime import date
from pathlib import Path
from urllib.parse import urlparse, unquote_plus
from bs4 import BeautifulSoup
from typing import Optional

# ── Constants ─────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "DNT": "1",
}

REQUEST_TIMEOUT = 15
MAX_RETRIES = 3
MAX_BODY_LINES = 600


# ── Search engines ────────────────────────────────────────────────────────────

def search_duckduckgo(query: str, num: int) -> list:
    """Search via DuckDuckGo — no API key required."""
    # Try newer package name first, fall back to legacy name
    DDGS = None
    try:
        from ddgs import DDGS
    except ImportError:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            print("Run: pip install ddgs")
            sys.exit(1)

    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=num):
            url = r.get("href") or r.get("url", "")
            if url:
                results.append(url)
    return results


def search_google_api(query: str, num: int, api_key: str, cx: str) -> list:
    """
    Search via Google Custom Search JSON API.
    Get a free key at: https://developers.google.com/custom-search/v1/overview
    Free tier: 100 queries/day, 10 results/request => 10 requests for 100 results.
    """
    base = "https://www.googleapis.com/customsearch/v1"
    results = []
    for start in range(1, min(num + 1, 101), 10):  # max 100 from API
        params = {"key": api_key, "cx": cx, "q": query, "start": start, "num": 10}
        try:
            r = requests.get(base, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            for item in data.get("items", []):
                results.append(item["link"])
        except Exception as exc:
            print(f"  Google API error at start={start}: {exc}")
            break
        time.sleep(0.5)
    return results[:num]


# ── Text utilities ────────────────────────────────────────────────────────────

def slugify(text: str, max_len: int = 60) -> str:
    text = str(text).lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:max_len].rstrip("-")


def extract_year(text: str) -> Optional[str]:
    m = re.search(r"\b(19|20)\d{2}\b", text or "")
    return m.group(0) if m else None


def clean_title(raw: str) -> str:
    return re.sub(r"\s*[\|\-–—]\s*[^|\-–—]{1,60}$", "", raw).strip()


# ── Metadata extraction ───────────────────────────────────────────────────────

def _meta(soup: BeautifulSoup, **attrs) -> str:
    tag = soup.find("meta", attrs=attrs)
    return (tag.get("content") or "").strip() if tag else ""


def get_title(soup: BeautifulSoup) -> str:
    h1 = soup.find("h1")
    if h1:
        text = h1.get_text(strip=True)
        if text:
            return text
    t = soup.find("title")
    return clean_title(t.get_text(strip=True)) if t else "Untitled"


def get_description(soup: BeautifulSoup) -> str:
    for k, v in [("name", "description"), ("property", "og:description"),
                 ("name", "twitter:description")]:
        desc = _meta(soup, **{k: v})
        if desc:
            return desc
    return ""


def get_keywords(soup: BeautifulSoup) -> list:
    raw = _meta(soup, name="keywords")
    if not raw:
        return []
    return [slugify(k) for k in raw.split(",") if k.strip()][:8]


def get_author(soup: BeautifulSoup, url: str) -> str:
    for k, v in [("name", "author"), ("property", "article:author"),
                 ("name", "twitter:creator")]:
        val = _meta(soup, **{k: v})
        if val and not val.startswith("http"):
            parts = val.strip().split()
            return slugify(parts[-1]) if parts else "unknown"
    link = soup.find("a", rel="author")
    if link:
        parts = link.get_text(strip=True).split()
        return slugify(parts[-1]) if parts else "unknown"
    domain = urlparse(url).netloc.replace("www.", "").split(".")[0]
    return slugify(domain)


def get_year(soup: BeautifulSoup) -> str:
    for k, v in [("property", "article:published_time"), ("name", "date"),
                 ("name", "pubdate"), ("itemprop", "datePublished")]:
        yr = extract_year(_meta(soup, **{k: v}))
        if yr:
            return yr
    t = soup.find("time")
    if t:
        yr = extract_year(t.get("datetime", "") or t.get_text())
        if yr:
            return yr
    return str(date.today().year)


def get_type(url: str, soup: BeautifulSoup) -> str:
    academic = ["arxiv.org", "doi.org", "pubmed.ncbi", "scholar.google",
                "researchgate.net", "academia.edu", "springer.com",
                "ieee.org", "acm.org", "nature.com", "sciencedirect.com"]
    if any(a in url for a in academic):
        return "source"
    if (soup.find("meta", attrs={"name": "author"}) or
            soup.find("meta", attrs={"property": "article:author"})):
        return "source"
    return "concept"


# ── Content processing ────────────────────────────────────────────────────────

def html_to_md(html: str) -> str:
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    h.body_width = 0
    h.protect_links = True
    h.wrap_links = False
    h.ignore_tables = False
    return h.handle(html)


def get_main_content(soup: BeautifulSoup):
    for tag in soup(["script", "style", "nav", "footer", "header",
                     "aside", "noscript", "form", "iframe"]):
        tag.decompose()
    return (
        soup.find("article") or
        soup.find("main") or
        soup.find(id=re.compile(r"content|main|article", re.I)) or
        soup.find(class_=re.compile(r"content|main|article|post|entry", re.I)) or
        soup.find("body") or
        soup
    )


def bold_first_terms(body: str, terms: list) -> str:
    """Bold first occurrence of each keyword term in the article body."""
    for term in terms:
        if len(term) < 3:
            continue
        pat = r"(?<!\*\*)\b(" + re.escape(term) + r")\b(?!\*\*)"
        body, _ = re.subn(pat, r"**\1**", body, count=1, flags=re.IGNORECASE)
    return body


def add_wikilinks_per_section(markdown: str, title_map: dict) -> str:
    """
    For each markdown section (split at H1-H3 headings), replace the first
    occurrence of any known article title with [[wikilink]] syntax.
    """
    sections = re.split(r"(?=^#{1,3} )", markdown, flags=re.MULTILINE)
    result = []
    for section in sections:
        for title in title_map:
            if len(title) < 5:
                continue
            pat = r"(?<!\[)\b(" + re.escape(title) + r")\b(?!\])"
            section, _ = re.subn(pat, r"[[\1]]", section, count=1, flags=re.IGNORECASE)
        result.append(section)
    return "".join(result)


# ── File naming & frontmatter ─────────────────────────────────────────────────

def build_filename(metadata: dict) -> str:
    title_slug = slugify(metadata["title"], max_len=50)
    if metadata["type"] == "source":
        author = metadata.get("author", "unknown")
        year = metadata.get("year", str(date.today().year))
        short = slugify(metadata["title"], max_len=35)
        return f"{author}-{year}-{short}.md"
    return f"{title_slug}.md"


def build_frontmatter(meta: dict) -> str:
    today = str(date.today())
    fm = {
        "title": meta.get("title", "Untitled"),
        "date_created": today,
        "date_modified": today,
        "summary": meta.get("summary", ""),
        "tags": meta.get("tags", []),
        "type": meta.get("type", "concept"),
        "status": "draft",
    }
    return "---\n" + yaml.dump(fm, default_flow_style=False, allow_unicode=True).rstrip() + "\n---\n\n"


# ── HTTP ──────────────────────────────────────────────────────────────────────

def fetch_page(url: str, session: requests.Session, delay: float) -> Optional[requests.Response]:
    for attempt in range(MAX_RETRIES):
        try:
            resp = session.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT,
                               allow_redirects=True)
            resp.raise_for_status()
            ct = resp.headers.get("Content-Type", "")
            if "text/html" not in ct and "text/plain" not in ct:
                print(f"  [skip] Non-HTML content-type: {ct[:40]}")
                return None
            # Detect JS-only pages (Google, Cloudflare, etc.)
            if len(resp.text) < 1000 and (
                "enablejs" in resp.text or "javascript" in resp.text.lower()[:200]
            ):
                print("  [skip] JS-only page — no static content")
                return None
            return resp
        except requests.exceptions.TooManyRedirects:
            print("  [skip] Too many redirects")
            return None
        except Exception as exc:
            wait = delay * (attempt + 1)
            print(f"  [retry {attempt+1}] {exc}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(wait)
    return None


# ── Scraper ───────────────────────────────────────────────────────────────────

def scrape(url: str, session: requests.Session, delay: float) -> Optional[dict]:
    resp = fetch_page(url, session, delay)
    if resp is None:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    title = get_title(soup)
    description = get_description(soup)
    keywords = get_keywords(soup)
    author = get_author(soup, url)
    year = get_year(soup)
    page_type = get_type(url, soup)

    content_node = get_main_content(soup)
    body_md = html_to_md(str(content_node))

    lines = body_md.splitlines()
    if len(lines) > MAX_BODY_LINES:
        body_md = "\n".join(lines[:MAX_BODY_LINES]) + "\n\n*[Content truncated]*\n"

    summary = description or (body_md.replace("\n", " ").strip()[:220] + "...")

    return {
        "url": url,
        "title": title,
        "summary": summary,
        "tags": keywords,
        "type": page_type,
        "author": author,
        "year": year,
        "body": body_md,
    }


# ── Filename dedup ────────────────────────────────────────────────────────────

def unique_filename(base: str, output_dir: Path, used: set) -> str:
    candidate = base
    stem = base[:-3]
    n = 2
    while candidate in used or (output_dir / candidate).exists():
        candidate = f"{stem}-{n}.md"
        n += 1
    used.add(candidate)
    return candidate


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run(query: str, num: int, output_dir: Path, delay: float,
        engine: str, google_api_key: str, google_cx: str) -> None:

    output_dir.mkdir(parents=True, exist_ok=True)

    # ── 0. Load existing log to skip already-scraped URLs ─────────────────────
    log_path = output_dir / "scrape-log.json"
    existing_log = []
    existing_urls: set = set()
    if log_path.exists():
        try:
            existing_log = json.loads(log_path.read_text(encoding="utf-8"))
            existing_urls = {entry["url"] for entry in existing_log}
            print(f"Loaded {len(existing_log)} existing log entries. Deduplicating ...\n")
        except Exception:
            pass

    # ── 1. Collect URLs ───────────────────────────────────────────────────────
    print(f'\nSearching ({engine}) for: "{query}"  (target: {num})\n')

    if engine == "google":
        if not google_api_key or not google_cx:
            print("ERROR: --engine google requires --google-api-key and --google-cx")
            print("       Get a free key at: https://developers.google.com/custom-search/v1")
            sys.exit(1)
        urls = search_google_api(query, num, google_api_key, google_cx)
    else:
        urls = search_duckduckgo(query, num)

    if not urls:
        print("No results returned. Try a different query or search engine.")
        sys.exit(0)

    urls_new = [u for u in urls if u not in existing_urls]
    skipped_count = len(urls) - len(urls_new)
    if skipped_count:
        print(f"Skipping {skipped_count} already-logged URL(s).")
    print(f"Found {len(urls_new)} new URL(s) to scrape.\n")

    if not urls_new:
        print("Nothing new to scrape.")
        return

    # ── 2. Scrape pages ───────────────────────────────────────────────────────
    session = requests.Session()
    session.headers.update(HEADERS)

    articles = []
    log = []
    used_filenames = {entry.get("file") for entry in existing_log if entry.get("file")}
    start_index = len(existing_log) + 1

    for i, url in enumerate(urls_new, start_index):
        print(f"[{i:3}/{len(urls)}] {url[:90]}")
        time.sleep(delay)

        data = scrape(url, session, delay)
        if data is None:
            log.append({"index": i, "url": url, "status": "failed"})
            print("         -> SKIPPED\n")
            continue

        filename = build_filename(data)
        filename = unique_filename(filename, output_dir, used_filenames)

        body = data["body"]
        if data["tags"]:
            body = bold_first_terms(body, data["tags"])

        full_content = (
            build_frontmatter(data)
            + f"> **Source:** [{url}]({url})\n\n"
            + body
        )

        (output_dir / filename).write_text(full_content, encoding="utf-8")
        print(f"         -> {filename}\n")

        articles.append({
            "index": i,
            "title": data["title"],
            "filename": filename,
            "url": url,
            "type": data["type"],
        })
        log.append({"index": i, "url": url, "status": "ok", "file": filename})

    # ── 3. Second pass: wikilinks ─────────────────────────────────────────────
    if len(articles) > 1:
        print("Adding cross-reference wikilinks ...")
        title_map = {a["title"]: a["filename"][:-3] for a in articles}

        for a in articles:
            fp = output_dir / a["filename"]
            content = fp.read_text(encoding="utf-8")
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) == 3:
                    fm_block = "---" + parts[1] + "---"
                    body = add_wikilinks_per_section(parts[2], title_map)
                    content = fm_block + body
            fp.write_text(content, encoding="utf-8")

    # ── 4. Index file ─────────────────────────────────────────────────────────
    today = str(date.today())
    index_lines = [
        "---",
        f'title: "Index -- {query}"',
        f"date_created: {today}",
        f"date_modified: {today}",
        f'summary: "Index of {len(articles)} articles scraped for: {query}"',
        "tags: [index, search-results]",
        "type: synthesis",
        "status: draft",
        "---",
        "",
        f"# Index: {query}",
        "",
        f"- **Query:** `{query}`",
        f"- **Engine:** {engine}",
        f"- **Scraped:** {today}",
        f"- **Total:** {len(articles)} articles saved, "
        f"{len(log) - len(articles)} failed",
        "",
        "## Articles",
        "",
        "| # | Title | Type | File |",
        "|---|-------|------|------|",
    ]
    for a in articles:
        index_lines.append(
            f"| {a['index']} | [[{a['title']}]] | `{a['type']}` "
            f"| [{a['filename']}]({a['filename']}) |"
        )

    (output_dir / "index.md").write_text("\n".join(index_lines), encoding="utf-8")
    combined_log = existing_log + log
    (output_dir / "scrape-log.json").write_text(
        json.dumps(combined_log, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    ok = sum(1 for e in log if e["status"] == "ok")
    print(f"\nDone.  {ok} saved  |  {len(log) - ok} failed")
    print(f"Output : {output_dir.resolve()}")
    print(f"Index  : {(output_dir / 'index.md').resolve()}")
    print(f"Log    : {(output_dir / 'scrape-log.json').resolve()}\n")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(
        description="Search the web, scrape each result, save structured Markdown.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Search engines:
  duckduckgo  (default) — no API key required, very reliable
  google      — requires --google-api-key and --google-cx
                Get a free key: https://developers.google.com/custom-search/v1

Examples:
  python bot.py "active inference"
  python bot.py "machine learning" -n 50 -o ./ml-articles --delay 3
  python bot.py "climate change" --engine google --google-api-key AIza... --google-cx 123...
        """,
    )
    p.add_argument("query", help="Search query (quote multi-word queries)")
    p.add_argument("-n", "--num", type=int, default=100,
                   help="Number of results (default: 100)")
    p.add_argument("-o", "--output", default="scraped-articles",
                   help="Output directory (default: ./scraped-articles)")
    p.add_argument("--delay", type=float, default=1.5,
                   help="Seconds between page requests (default: 1.5)")
    p.add_argument("--engine", choices=["duckduckgo", "google"], default="duckduckgo",
                   help="Search engine to use (default: duckduckgo)")
    p.add_argument("--google-api-key", default="",
                   help="Google Custom Search JSON API key (required for --engine google)")
    p.add_argument("--google-cx", default="",
                   help="Google Custom Search Engine ID (required for --engine google)")
    args = p.parse_args()

    run(
        query=args.query,
        num=args.num,
        output_dir=Path(args.output),
        delay=args.delay,
        engine=args.engine,
        google_api_key=args.google_api_key,
        google_cx=args.google_cx,
    )


if __name__ == "__main__":
    main()
