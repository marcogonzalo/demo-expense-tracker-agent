"""Fase 1: ingest CSV, categorize with Jev Choice (or fallback), persist."""

from __future__ import annotations

from typing import Any

from src.agent import Agent
from src.config import EXPENSE_CATEGORIES, EXPENSES_CSV, OPENROUTER_API_KEY
from src.db import movement_key, upsert_movement
from src.decisions import DecisionError, choice
from src.tools import read_expenses_csv


def fallback_category(concept: str, amount: float) -> str:
    """Deterministic category when Decisions API is unavailable."""
    text = concept.lower()
    if amount > 0:
        return "Ingresos"
    rules: list[tuple[tuple[str, ...], str]] = [
        (("alquiler", "habitación", "habitacion", "hipoteca"), "Vivienda"),
        (("teléfono", "telefono", "internet", "luz", "agua", "gas"), "Servicios"),
        (("supermercado", "mercadona", "comida", "grocery"), "Alimentacion"),
        (("transporte", "metro", "bus", "abono", "gasolina"), "Transporte"),
        (
            (
                "cine",
                "restaurante",
                "cena",
                "bar",
                "tapas",
                "café",
                "cafe",
                "concierto",
                "terraza",
                "helado",
                "copas",
                "vermut",
                "sushi",
                "pizza",
                "escape",
                "patinaje",
                "halloween",
                "exposición",
                "exposicion",
            ),
            "Ocio",
        ),
        (
            (
                "camiseta",
                "pantalones",
                "auriculares",
                "monitor",
                "teclado",
                "abrigo",
                "botas",
                "smartwatch",
                "tablet",
                "altavoz",
                "chaqueta",
                "zapatillas",
                "funda",
                "mediamarkt",
                "fnac",
                "pccomponentes",
                "zara",
                "amazon",
                "samsung",
                "worten",
                "mango",
                "nike",
                "corte inglés",
                "corte ingles",
                "outlet",
            ),
            "Compras",
        ),
    ]
    for keywords, category in rules:
        if any(k in text for k in keywords):
            return category
    return "Otros"


def categorize_movement(concept: str, amount: float, date: str) -> tuple[str, float]:
    """Return (category, confidence) via Jev Choice or fallback."""
    if not OPENROUTER_API_KEY:
        cat = fallback_category(concept, amount)
        return cat, 1.0

    try:
        selected, confidence = choice(
            {
                "date": date,
                "concept": concept,
                "amount": amount,
                "sign": "income" if amount > 0 else "expense",
            },
            instructions=(
                "Assign exactly one expense category to this bank movement. "
                "Positive amounts are income."
            ),
            criteria=EXPENSE_CATEGORIES,
            question_id="category",
        )
        if selected not in EXPENSE_CATEGORIES:
            return fallback_category(concept, amount), confidence
        return selected, confidence
    except DecisionError:
        return fallback_category(concept, amount), 0.0


class IngesterAgent(Agent):
    """Import CSV rows into TinyDB with categories."""

    def __init__(self) -> None:
        super().__init__(
            system_prompt="You ingest and categorize bank movements.",
            max_iterations=4,
            max_tool_calls=50,
            tools={"read_expenses_csv": read_expenses_csv},
        )

    def ingest(self, csv_relative_path: str = EXPENSES_CSV) -> dict[str, int]:
        """Read CSV, categorize, upsert. Returns insert/update counts."""
        rows = self.call_tool("read_expenses_csv", relative_path=csv_relative_path)
        inserted = 0
        updated = 0
        for row in rows:
            category, confidence = categorize_movement(
                row["concept"], row["amount"], row["date"]
            )
            record: dict[str, Any] = {
                "id": movement_key(row["date"], row["concept"], row["amount"]),
                "date": row["date"],
                "concept": row["concept"],
                "amount": row["amount"],
                "category": category,
                "category_confidence": confidence,
            }
            if upsert_movement(record):
                inserted += 1
            else:
                updated += 1
        print("inserted", inserted)
        print("updated", updated)
        return {"inserted": inserted, "updated": updated, "total": len(rows)}


def main() -> None:
    agent = IngesterAgent()
    result = agent.ingest()
    print("ingest_result", result)


if __name__ == "__main__":
    main()
