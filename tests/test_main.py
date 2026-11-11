"""Smoke tests for the FastAPI entrypoint skeleton."""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

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


if __name__ == "__main__":
    unittest.main()
