"""TDD: TinyDB idempotent upserts."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.db import list_movements, movement_key, reset_db_cache, upsert_movement


class TestDbIdempotency(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "db.json"
        reset_db_cache()

    def tearDown(self) -> None:
        reset_db_cache()
        self.tmp.cleanup()

    def test_movement_key_stable(self) -> None:
        a = movement_key("2026-06-01", "Nómina", 1350.0)
        b = movement_key("2026-06-01", "Nómina", 1350.0)
        self.assertEqual(a, b)

    def test_reimport_does_not_duplicate(self) -> None:
        record = {
            "date": "2026-06-01",
            "concept": "Nómina",
            "amount": 1350.0,
            "category": "Ingresos",
        }
        self.assertTrue(upsert_movement(record, path=self.db_path))
        self.assertFalse(upsert_movement(record, path=self.db_path))
        rows = list_movements(path=self.db_path)
        self.assertEqual(len(rows), 1)


if __name__ == "__main__":
    unittest.main()
