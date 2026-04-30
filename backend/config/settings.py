"""
Central configuration — all paths and env-driven settings live here
so the rest of the app never hard-codes a directory name.
"""

import os
from pathlib import Path

# Articles are stored relative to the project root (where uvicorn is run from)
SCRAPED_DIR = Path(os.getenv("SCRAPED_DIR", "scraped-articles"))
SAVED_FILE = Path(os.getenv("SAVED_FILE", "saved_articles.json"))

# Location of the bot script — resolved from this file's location so it works
# regardless of the shell working directory
BOT_SCRIPT = Path(__file__).resolve().parents[1] / "services" / "bot.py"

# Seconds before a bot subprocess is forcibly killed
BOT_TIMEOUT = int(os.getenv("BOT_TIMEOUT", "300"))

# Set AUTO_GIT_PUSH=true in .env to automatically push scraped commits
AUTO_GIT_PUSH = os.getenv("AUTO_GIT_PUSH", "false").lower() == "true"
