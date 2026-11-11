"""FastAPI HTTP entrypoint for the expense tracker agent demo."""

from __future__ import annotations

from fastapi import FastAPI

from src.config import APP_NAME, APP_VERSION, WORKDIR

print("WORKDIR", WORKDIR)

app = FastAPI(title=APP_NAME, version=APP_VERSION)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe used by Docker and local smoke checks."""
    return {"status": "ok", "service": APP_NAME, "version": APP_VERSION}


@app.get("/")
def root() -> dict[str, str]:
    """Minimal root so the HTTP surface exists from Fase 0 onward."""
    return {
        "message": "Expense tracker agent API",
        "docs": "/docs",
        "health": "/health",
    }
