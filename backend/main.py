"""
FastAPI application factory.
Run from the project root with: uvicorn backend.main:app --reload
(or via the thin root shim: uvicorn api:app --reload)
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.routes.articles import router as articles_router
from backend.routes.export import router as export_router
from backend.routes.saved import router as saved_router
from backend.routes.search import router as search_router

app = FastAPI(title="Search Bot API")

# CORS is wide-open because this is a personal tool accessed via Cloudflare Tunnel.
# If you ever expose this publicly, replace "*" with your exact frontend origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all route groups
app.include_router(articles_router)
app.include_router(saved_router)
app.include_router(search_router)
app.include_router(export_router)

# In production, serve the built React app from the same process
_frontend_dist = Path("frontend/dist")
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="static")
