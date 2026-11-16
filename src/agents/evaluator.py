"""Fase 3: evaluate expense necessity with Jev Score (or fallback)."""

from __future__ import annotations

from typing import Any

from src.agent import Agent
from src.config import NECESSITY_SCALE, OPENROUTER_API_KEY
from src.db import list_movements, update_movement_fields
from src.decisions import DecisionError, score
from src.tools import query_movements

_CATEGORY_DEFAULT_LEVEL: dict[str, int] = {
    "Vivienda": 1,
    "Servicios": 2,
    "Alimentacion": 2,
    "Transporte": 2,
    "Ocio": 4,
    "Compras": 5,
    "Ingresos": 1,
    "Otros": 3,
}


def fallback_necessity(category: str, amount: float, concept: str) -> int:
    """Deterministic necessity level 1–5 when Decisions API is unavailable."""
    base = _CATEGORY_DEFAULT_LEVEL.get(category, 3)
    text = concept.lower()
    # Large retail / tech purchases skew toward unnecessary.
    if category == "Compras" and abs(amount) >= 80:
        return 5
    if category == "Ocio" and abs(amount) >= 50:
        return 5
    if any(k in text for k in ("smartwatch", "tablet", "monitor", "auriculares inalámbricos")):
        return 5
    return base


def score_to_level(weighted_score: float, criteria_len: int) -> int:
    """Map 0-indexed weighted score to 1-based necessity level."""
    idx = int(round(weighted_score))
    idx = max(0, min(criteria_len - 1, idx))
    return idx + 1


def evaluate_necessity(movement: dict[str, Any]) -> tuple[int, float]:
    """Return (necessity_level, confidence) for one expense movement."""
    category = str(movement.get("category", "Otros"))
    amount = float(movement.get("amount", 0))
    concept = str(movement.get("concept", ""))

    if amount >= 0:
        return 1, 1.0

    if not OPENROUTER_API_KEY:
        return fallback_necessity(category, amount, concept), 1.0

    criteria = [
        f"{level}: {meta['label']} — {meta['description']}"
        for level, meta in sorted(NECESSITY_SCALE.items())
    ]
    try:
        weighted, confidence = score(
            {
                "date": movement.get("date"),
                "concept": concept,
                "amount": amount,
                "category": category,
            },
            instructions=(
                "Rate how necessary this expense is on the ordered scale. "
                "Lower scores mean more indispensable; higher scores mean unnecessary."
            ),
            criteria=criteria,
            question_id="necessity",
        )
        level = score_to_level(weighted, len(criteria))
        return level, confidence
    except DecisionError:
        return fallback_necessity(category, amount, concept), 0.0


class EvaluatorAgent(Agent):
    """Assign necessity_level to all expense movements in TinyDB."""

    def __init__(self) -> None:
        super().__init__(
            system_prompt="You evaluate necessity of expenses on a 1-5 scale.",
            max_iterations=4,
            max_tool_calls=200,
            tools={"query_movements": query_movements},
        )

    def evaluate_all(self) -> dict[str, int]:
        expenses = self.call_tool("query_movements", expenses_only=True)
        updated = 0
        for movement in expenses:
            level, confidence = evaluate_necessity(movement)
            ok = update_movement_fields(
                str(movement["id"]),
                {
                    "necessity_level": level,
                    "necessity_confidence": confidence,
                },
            )
            if ok:
                updated += 1
        print("evaluated", updated)
        return {"evaluated": updated, "total_expenses": len(expenses)}


def main() -> None:
    agent = EvaluatorAgent()
    result = agent.evaluate_all()
    print("evaluate_result", result)


if __name__ == "__main__":
    main()
