"""Auth dependency — all /api/* routes require a matching X-API-Key header."""

from fastapi import Header, HTTPException
from backend.config.settings import API_SECRET


def verify_api_key(x_api_key: str = Header(default="")) -> None:
    # If no secret is configured, the check is skipped (dev convenience).
    # In production always set API_SECRET in .env.
    if API_SECRET and x_api_key != API_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")
