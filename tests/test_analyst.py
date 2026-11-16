"""TDD: analyst summary + fallback report."""

from __future__ import annotations

import unittest

from src.agents.analyst import build_summary, fallback_report


class TestAnalyst(unittest.TestCase):
    def test_build_summary_detects_november_burst(self) -> None:
        movements = [
            {
                "date": "2026-06-01",
                "concept": "Nómina",
                "amount": 1350.0,
                "category": "Ingresos",
            },
            {
                "date": "2026-06-02",
                "concept": "Alquiler",
                "amount": -700.0,
                "category": "Vivienda",
                "necessity_level": 1,
            },
            {
                "date": "2026-11-28",
                "concept": "Tablet",
                "amount": -219.0,
                "category": "Compras",
                "necessity_level": 5,
            },
        ]
        summary = build_summary(movements)
        self.assertEqual(summary["discretionary_november_count"], 1)
        self.assertEqual(summary["discretionary_november_total"], 219.0)

    def test_fallback_report_has_three_blocks(self) -> None:
        summary = {
            "avg_monthly_savings_jun_oct": 100.0,
            "november_savings": -50.0,
            "discretionary_november_total": 400.0,
            "discretionary_november_count": 4,
        }
        report = fallback_report(summary)
        self.assertIn("patterns", report)
        self.assertIn("excesses", report)
        self.assertIsInstance(report["actions"], list)
        self.assertGreaterEqual(len(report["actions"]), 1)


if __name__ == "__main__":
    unittest.main()
