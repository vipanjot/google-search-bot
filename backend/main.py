"""
FastAPI application factory.
Run from the project root with: uvicorn backend.main:app --reload
(or via the thin root shim: uvicorn api:app --reload)
"""

from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.middleware.auth import verify_api_key
from backend.routes.articles import router as articles_router
from backend.routes.export import router as export_router
from backend.routes.saved import router as saved_router
from backend.routes.search import router as search_router

app = FastAPI(title="Search Bot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://searchbot.pages.dev"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*", "X-API-Key"],
)

# All API routes require a valid X-API-Key header (set API_SECRET in .env)
_auth = [Depends(verify_api_key)]
app.include_router(articles_router, dependencies=_auth)
app.include_router(saved_router, dependencies=_auth)
app.include_router(search_router, dependencies=_auth)
app.include_router(export_router, dependencies=_auth)

# In production, serve the built React app from the same process
_frontend_dist = Path("frontend/dist")
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="static")
