"""
Thin entry point — keeps `uvicorn api:app` working after the backend
was moved into the backend/ package.
"""

from backend.main import app  # noqa: F401 — re-exported for uvicorn
