"""Export route — bundle all scraped articles into a downloadable ZIP."""

import io
import zipfile

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.config.settings import SAVED_FILE, SCRAPED_DIR

router = APIRouter()


@router.get("/api/export/zip")
def export_zip():
    """
    Stream all .md files plus saved_articles.json as a single ZIP.
    StreamingResponse avoids loading the entire archive into memory before sending.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        if SCRAPED_DIR.exists():
            for f in sorted(SCRAPED_DIR.glob("*.md")):
                zf.write(f, f"scraped-articles/{f.name}")
        if SAVED_FILE.exists():
            zf.write(SAVED_FILE, "saved_articles.json")
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="searchbot-articles.zip"'},
    )
