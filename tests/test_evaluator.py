"""TDD: necessity scoring helpers."""

from __future__ import annotations

import unittest

from src.agents.evaluator import fallback_necessity, score_to_level


class TestEvaluator(unittest.TestCase):
    def test_score_to_level_bounds(self) -> None:
        self.assertEqual(score_to_level(0.0, 5), 1)
        self.assertEqual(score_to_level(4.0, 5), 5)
        self.assertEqual(score_to_level(1.6, 5), 3)

    def test_fallback_housing_indispensable(self) -> None:
        self.assertEqual(fallback_necessity("Vivienda", -700.0, "Alquiler"), 1)

    def test_fallback_big_purchase_unnecessary(self) -> None:
        self.assertEqual(
            fallback_necessity("Compras", -219.0, "Tablet Samsung Store"),
            5,
        )


if __name__ == "__main__":
    unittest.main()
