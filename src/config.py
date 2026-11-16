"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

WORKDIR = Path(os.getenv("WORKDIR", "/data")).resolve()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api")
APP_NAME = "Demo Expense Tracker Agent"
APP_VERSION = "0.1.0"

# Chat / reasoning models (System Two)
CHAT_MODEL = os.getenv("CHAT_MODEL", "google/gemini-2.5-flash")
ANALYST_MODEL = os.getenv("ANALYST_MODEL", "deepseek/deepseek-r1")

# Decision model (System One — Jev)
DECISION_MODEL = os.getenv("DECISION_MODEL", "typesafe/jev-1.14")

EXPENSE_CATEGORIES: dict[str, str] = {
    "Vivienda": "Rent, mortgage, housing-related fixed costs.",
    "Servicios": "Phone, internet, utilities, subscriptions.",
    "Alimentacion": "Groceries and supermarket purchases.",
    "Transporte": "Public transit, fuel, commuting passes.",
    "Ocio": "Restaurants, bars, cinema, leisure activities.",
    "Compras": "Clothes, electronics, one-off retail purchases.",
    "Ingresos": "Salary, refunds, positive transfers.",
    "Otros": "Anything that does not fit the categories above.",
}

NECESSITY_SCALE: dict[int, dict[str, str]] = {
    1: {
        "label": "Indispensable",
        "description": "Essential for basic living: rent, core utilities, staple food.",
        "color": "#22c55e",
    },
    2: {
        "label": "Necesario",
        "description": "Important recurring need with little flexibility (transport, phone).",
        "color": "#84cc16",
    },
    3: {
        "label": "Conveniente",
        "description": "Useful but deferrable; quality-of-life without being mandatory.",
        "color": "#eab308",
    },
    4: {
        "label": "Discrecional",
        "description": "Optional spend driven by preference rather than need.",
        "color": "#f97316",
    },
    5: {
        "label": "Innecesario",
        "description": "Impulse or luxury purchase that could be skipped without impact.",
        "color": "#ef4444",
    },
}

DB_PATH = WORKDIR / "db.json"
EXPENSES_CSV = "expenses_log.csv"
