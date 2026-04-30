"""Pydantic request/response models for the API."""

from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    num: int = 20
    engine: str = "duckduckgo"
    output_dir: str = "scraped-articles"
    # Google Custom Search — only required when engine="google"
    google_api_key: str = ""
    google_cx: str = ""
