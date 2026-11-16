"""Smoke + API tests for the FastAPI surface."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from src.db import reset_db_cache
from src.main import app


class TestMainApp(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_health_returns_ok(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertIn("version", payload)

    def test_root_exposes_docs_hint(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["docs"], "/docs")
        self.assertEqual(payload["health"], "/health")

    def test_necessity_scale_endpoint(self) -> None:
        response = self.client.get("/api/necessity-scale")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("1", data)
        self.assertEqual(data["1"]["label"], "Indispensable")


class TestPipelineApi(unittest.TestCase):
    def test_pipeline_with_temp_workdir(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        workdir = Path(tmp.name)
        # Use a tiny CSV for speed.
        (workdir / "expenses_log.csv").write_text(
            "date,concept,amount\n"
            "2026-06-01,Nómina mensual,+1350.00\n"
            "2026-06-02,Alquiler habitación,-700.00\n"
            "2026-11-28,Tablet Samsung Store,-219.00\n",
            encoding="utf-8",
        )
        db_path = workdir / "db.json"
        reset_db_cache()

        with (
            mock.patch("src.tools.WORKDIR", workdir),
            mock.patch("src.db.DB_PATH", db_path),
            mock.patch("src.config.OPENROUTER_API_KEY", ""),
            mock.patch("src.agents.ingester.OPENROUTER_API_KEY", ""),
            mock.patch("src.agents.evaluator.OPENROUTER_API_KEY", ""),
            mock.patch("src.agents.analyst.OPENROUTER_API_KEY", ""),
        ):
            client = TestClient(app)
            response = client.post("/api/pipeline")
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["ingest"]["inserted"], 3)
            self.assertGreaterEqual(payload["evaluate"]["evaluated"], 2)
            self.assertIn("report", payload["analyze"])
            metrics = client.get("/api/metrics")
            self.assertEqual(metrics.status_code, 200)
            self.assertGreater(metrics.json()["total_expense"], 0)

        reset_db_cache()


if __name__ == "__main__":
    unittest.main()
