"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

WORKDIR = Path(os.getenv("WORKDIR", "/data")).resolve()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
APP_NAME = "Demo Expense Tracker Agent"
APP_VERSION = "0.1.0"

# Populated in later phases; kept here so the final project shape stays stable.
NECESSITY_SCALE: dict[int, dict[str, str]] = {}
