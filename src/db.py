"""TinyDB persistence with deterministic unique keys (idempotent imports)."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from tinydb import Query, TinyDB

from src.config import DB_PATH

_db: TinyDB | None = None


def movement_key(date: str, concept: str, amount: float) -> str:
    """Deterministic unique key for a movement."""
    payload = f"{date}|{concept}|{amount:.2f}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def get_db(path: Path | None = None) -> TinyDB:
    """Return a TinyDB instance (cached for the default path)."""
    global _db
    db_path = path or DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if path is None:
        if _db is None:
            _db = TinyDB(db_path)
        return _db
    return TinyDB(db_path)


def reset_db_cache() -> None:
    """Close and clear the cached default DB (tests)."""
    global _db
    if _db is not None:
        _db.close()
        _db = None


def upsert_movement(record: dict[str, Any], *, path: Path | None = None) -> bool:
    """Insert or update a movement by its deterministic key.

    Returns True when a new document was inserted, False when updated/skipped.
    """
    key = record.get("id") or movement_key(
        str(record["date"]),
        str(record["concept"]),
        float(record["amount"]),
    )
    payload = {**record, "id": key}
    db = get_db(path)
    Movement = Query()
    existing = db.get(Movement.id == key)
    print("upsert_key", key)
    if existing is None:
        db.insert(payload)
        return True
    db.update(payload, Movement.id == key)
    return False


def list_movements(*, path: Path | None = None) -> list[dict[str, Any]]:
    """Return all movements sorted by date then concept."""
    db = get_db(path)
    rows = list(db.all())
    rows.sort(key=lambda r: (str(r.get("date", "")), str(r.get("concept", ""))))
    return rows


def update_movement_fields(
    movement_id: str,
    fields: dict[str, Any],
    *,
    path: Path | None = None,
) -> bool:
    """Patch fields on an existing movement. Returns True if found."""
    db = get_db(path)
    Movement = Query()
    updated = db.update(fields, Movement.id == movement_id)
    return bool(updated)


def clear_movements(*, path: Path | None = None) -> None:
    """Remove all movements (tests / reset)."""
    db = get_db(path)
    db.truncate()
