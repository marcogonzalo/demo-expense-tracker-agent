"""File and database tools with WORKDIR confinement."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from src.config import WORKDIR
from src.db import list_movements


class PathTraversalError(ValueError):
    """Raised when a resolved path escapes WORKDIR."""


def resolve_under_workdir(relative_path: str) -> Path:
    """Resolve a path and ensure it stays inside WORKDIR.

    Rejects absolute paths outside WORKDIR and any `..` escape after resolve.
    """
    raw = Path(relative_path)
    print("relative_path", relative_path)

    # Absolute paths must still land under WORKDIR after resolve.
    candidate = raw if raw.is_absolute() else (WORKDIR / raw)
    resolved = candidate.resolve()

    try:
        resolved.relative_to(WORKDIR)
    except ValueError as exc:
        raise PathTraversalError(
            f"Path escapes WORKDIR ({WORKDIR}): {relative_path}"
        ) from exc

    return resolved


def read_expenses_csv(relative_path: str) -> list[dict[str, Any]]:
    """Read CSV movements from a path confined to WORKDIR."""
    path = resolve_under_workdir(relative_path)
    if not path.is_file():
        raise FileNotFoundError(f"CSV not found: {path}")

    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            amount_raw = str(row.get("amount", "")).strip().replace(",", ".")
            amount = float(amount_raw)
            rows.append(
                {
                    "date": str(row.get("date", "")).strip(),
                    "concept": str(row.get("concept", "")).strip(),
                    "amount": amount,
                }
            )
    print("csv_rows", len(rows))
    return rows


def query_movements(
    *,
    category: str | None = None,
    expenses_only: bool = False,
) -> list[dict[str, Any]]:
    """Query TinyDB movements, optionally filtered."""
    movements = list_movements()
    if category:
        movements = [m for m in movements if m.get("category") == category]
    if expenses_only:
        movements = [m for m in movements if float(m.get("amount", 0)) < 0]
    return movements
