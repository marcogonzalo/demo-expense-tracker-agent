"""TDD: categorization fallback + ingest idempotency."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.agents.ingester import IngesterAgent, fallback_category
from src.db import list_movements, reset_db_cache


class TestIngester(unittest.TestCase):
    def test_fallback_income(self) -> None:
        self.assertEqual(fallback_category("Nómina mensual", 1350.0), "Ingresos")

    def test_fallback_rent(self) -> None:
        self.assertEqual(fallback_category("Alquiler habitación", -700.0), "Vivienda")

    def test_fallback_tech_purchase(self) -> None:
        self.assertEqual(
            fallback_category("Smartwatch Amazon", -149.0),
            "Compras",
        )

    def test_ingest_idempotent(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        workdir = Path(tmp.name)
        csv_path = workdir / "expenses_log.csv"
        csv_path.write_text(
            "date,concept,amount\n"
            "2026-06-01,Nómina mensual,+1350.00\n"
            "2026-06-02,Alquiler habitación,-700.00\n",
            encoding="utf-8",
        )
        db_path = workdir / "db.json"
        reset_db_cache()

        with (
            mock.patch("src.tools.WORKDIR", workdir),
            mock.patch("src.db.DB_PATH", db_path),
            mock.patch("src.agents.ingester.OPENROUTER_API_KEY", ""),
        ):
            agent = IngesterAgent()
            first = agent.ingest("expenses_log.csv")
            second = agent.ingest("expenses_log.csv")
            rows = list_movements(path=db_path)

        self.assertEqual(first["inserted"], 2)
        self.assertEqual(second["inserted"], 0)
        self.assertEqual(second["updated"], 2)
        self.assertEqual(len(rows), 2)
        reset_db_cache()


if __name__ == "__main__":
    unittest.main()
