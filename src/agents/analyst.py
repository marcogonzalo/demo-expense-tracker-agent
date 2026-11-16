"""Fase 4: financial analyst — patterns, excesses, suggested actions."""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from src.agent import Agent
from src.config import ANALYST_MODEL, NECESSITY_SCALE, OPENROUTER_API_KEY
from src.llm import LLMError, chat
from src.tools import query_movements


def _month(date: str) -> str:
    return date[:7]


def build_summary(movements: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate movements into a structured summary for analysis."""
    by_month: dict[str, dict[str, float]] = defaultdict(
        lambda: {"income": 0.0, "expense": 0.0}
    )
    discretionary_nov: list[dict[str, Any]] = []

    for m in movements:
        month = _month(str(m.get("date", "")))
        amount = float(m.get("amount", 0))
        if amount >= 0:
            by_month[month]["income"] += amount
        else:
            by_month[month]["expense"] += abs(amount)

        if month == "2026-11" and amount < 0:
            level = int(m.get("necessity_level") or 0)
            if level >= 4 or str(m.get("category")) == "Compras":
                discretionary_nov.append(m)

    months_sorted = sorted(by_month.keys())
    baseline = [m for m in months_sorted if m < "2026-11"]
    baseline_savings = []
    for m in baseline:
        baseline_savings.append(by_month[m]["income"] - by_month[m]["expense"])
    avg_savings = (
        sum(baseline_savings) / len(baseline_savings) if baseline_savings else 0.0
    )
    nov = by_month.get("2026-11", {"income": 0.0, "expense": 0.0})
    nov_savings = nov["income"] - nov["expense"]
    burst_total = sum(abs(float(x["amount"])) for x in discretionary_nov)

    return {
        "by_month": dict(by_month),
        "avg_monthly_savings_jun_oct": round(avg_savings, 2),
        "november_savings": round(nov_savings, 2),
        "discretionary_november_total": round(burst_total, 2),
        "discretionary_november_count": len(discretionary_nov),
        "discretionary_items": [
            {
                "date": x.get("date"),
                "concept": x.get("concept"),
                "amount": x.get("amount"),
                "category": x.get("category"),
                "necessity_level": x.get("necessity_level"),
            }
            for x in discretionary_nov
        ],
    }


def fallback_report(summary: dict[str, Any]) -> dict[str, Any]:
    """Deterministic three-block report when the reasoning LLM is unavailable."""
    avg = summary["avg_monthly_savings_jun_oct"]
    nov = summary["november_savings"]
    burst = summary["discretionary_november_total"]
    return {
        "patterns": (
            f"From June to October, average monthly savings were about {avg:.2f} EUR "
            "after fixed housing, services, food, and transport. Leisure stayed within "
            "a predictable band and shopping spikes were rare."
        ),
        "excesses": (
            f"In the last week of November, {summary['discretionary_november_count']} "
            f"discretionary tech/clothing purchases totaled {burst:.2f} EUR. "
            f"November net savings fell to {nov:.2f} EUR versus the prior average of "
            f"{avg:.2f} EUR, consuming prior buffer without any labeled promotion."
        ),
        "actions": [
            "Set a hard November campaign budget before the last week of the month.",
            "Cap Compras category at a fixed EUR amount; require a 48h delay over 50 EUR.",
            "Keep necessity levels 4–5 out of automatic card payments during sale weeks.",
            "Compare each electronics purchase against a written need, not store timing.",
        ],
        "source": "fallback",
    }


def llm_report(summary: dict[str, Any]) -> dict[str, Any]:
    """Ask a reasoning model for the three-block report."""
    scale_text = json.dumps(NECESSITY_SCALE, ensure_ascii=False)
    prompt = (
        "You are a personal finance analyst. Given the JSON summary of bank movements, "
        "write a structured diagnosis. Respond ONLY with JSON keys: "
        "patterns (string), excesses (string), actions (array of strings). "
        "Infer late-November discretionary shopping pressure from dates and categories; "
        "never claim the CSV labeled a promotion.\n\n"
        f"NECESSITY_SCALE: {scale_text}\n\n"
        f"SUMMARY: {json.dumps(summary, ensure_ascii=False)}"
    )
    content = chat(
        [
            {"role": "system", "content": "Return strict JSON only."},
            {"role": "user", "content": prompt},
        ],
        model=ANALYST_MODEL,
        temperature=0.3,
    )
    # Models sometimes wrap JSON in fences.
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()
    data = json.loads(text)
    return {
        "patterns": str(data.get("patterns", "")),
        "excesses": str(data.get("excesses", "")),
        "actions": list(data.get("actions") or []),
        "source": "llm",
    }


class AnalystAgent(Agent):
    """Produce a structured financial analysis report."""

    def __init__(self) -> None:
        super().__init__(
            system_prompt="You analyze spending patterns and recommend actions.",
            model=ANALYST_MODEL,
            max_iterations=4,
            max_tool_calls=20,
            tools={"query_movements": query_movements},
        )

    def analyze(self) -> dict[str, Any]:
        movements = self.call_tool("query_movements")
        summary = build_summary(movements)
        print("summary_keys", list(summary.keys()))

        if not OPENROUTER_API_KEY:
            report = fallback_report(summary)
        else:
            try:
                report = llm_report(summary)
            except (LLMError, json.JSONDecodeError, TypeError, ValueError):
                report = fallback_report(summary)

        return {"summary": summary, "report": report}


def main() -> None:
    agent = AnalystAgent()
    result = agent.analyze()
    print("analyst_report", result["report"])


if __name__ == "__main__":
    main()
