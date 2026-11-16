"""Aggregated metrics for the dashboard API."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from src.config import NECESSITY_SCALE
from src.db import list_movements


def enrich_movement(movement: dict[str, Any]) -> dict[str, Any]:
    """Attach necessity label/description from NECESSITY_SCALE when present."""
    enriched = dict(movement)
    level = movement.get("necessity_level")
    if level is not None:
        meta = NECESSITY_SCALE.get(int(level), {})
        enriched["necessity_label"] = meta.get("label")
        enriched["necessity_description"] = meta.get("description")
        enriched["necessity_color"] = meta.get("color")
    return enriched


def compute_metrics(movements: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Category spend percentages and monthly averages vs November peak."""
    rows = movements if movements is not None else list_movements()
    expenses = [m for m in rows if float(m.get("amount", 0)) < 0]

    by_category: dict[str, float] = defaultdict(float)
    by_month: dict[str, float] = defaultdict(float)
    for m in expenses:
        amount = abs(float(m["amount"]))
        category = str(m.get("category") or "Otros")
        month = str(m.get("date", ""))[:7]
        by_category[category] += amount
        by_month[month] += amount

    total_expense = sum(by_category.values()) or 1.0
    category_breakdown = [
        {
            "category": cat,
            "amount": round(amount, 2),
            "percentage": round(100.0 * amount / total_expense, 2),
        }
        for cat, amount in sorted(by_category.items(), key=lambda x: -x[1])
    ]

    months_sorted = sorted(by_month.keys())
    baseline_months = [m for m in months_sorted if m != "2026-11"]
    baseline_avg = (
        sum(by_month[m] for m in baseline_months) / len(baseline_months)
        if baseline_months
        else 0.0
    )
    november = by_month.get("2026-11", 0.0)

    return {
        "total_expense": round(sum(by_category.values()), 2),
        "category_breakdown": category_breakdown,
        "monthly_expense": {m: round(by_month[m], 2) for m in months_sorted},
        "average_monthly_expense_jun_oct": round(baseline_avg, 2),
        "november_expense": round(november, 2),
        "november_vs_average_delta": round(november - baseline_avg, 2),
        "movement_count": len(rows),
        "expense_count": len(expenses),
    }
