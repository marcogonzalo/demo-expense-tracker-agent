"""OpenRouter Decisions API client (Jev Choice / Score)."""

from __future__ import annotations

from typing import Any

import httpx

from src.config import DECISION_MODEL, OPENROUTER_API_KEY, OPENROUTER_BASE_URL


class DecisionError(RuntimeError):
    """Raised when a Decisions API call fails."""


def decide(
    state: dict[str, Any] | str | list[Any],
    questions: dict[str, Any],
    *,
    model: str | None = None,
    timeout: float = 60.0,
) -> dict[str, Any]:
    """Call POST /api/alpha/decisions and return the answers map."""
    if not OPENROUTER_API_KEY:
        raise DecisionError("OPENROUTER_API_KEY is not set")

    selected_model = model or DECISION_MODEL
    print("decision_model", selected_model)

    url = f"{OPENROUTER_BASE_URL.rstrip('/')}/alpha/decisions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/4Geeks/demo-expense-tracker-agent",
        "X-Title": "Demo Expense Tracker Agent",
    }
    payload = {
        "model": selected_model,
        "state": state,
        "questions": questions,
    }

    with httpx.Client(timeout=timeout) as client:
        response = client.post(url, headers=headers, json=payload)

    if response.status_code >= 400:
        raise DecisionError(
            f"Decisions API failed ({response.status_code}): {response.text}"
        )

    data = response.json()
    answers = data.get("answers")
    if not isinstance(answers, dict):
        raise DecisionError(f"Unexpected decisions response shape: {data}")
    return answers


def choice(
    state: dict[str, Any],
    *,
    instructions: str,
    criteria: dict[str, str],
    question_id: str = "category",
) -> tuple[str, float]:
    """Ask a Choice question; return (selected_option, confidence)."""
    answers = decide(
        state,
        {
            question_id: {
                "type": "choice",
                "instructions": instructions,
                "criteria": criteria,
            }
        },
    )
    answer = answers[question_id]
    selected = str(answer["choice"])
    confidence = float(answer.get("confidence") or 0.0)
    print("choice_selected", selected)
    return selected, confidence


def score(
    state: dict[str, Any],
    *,
    instructions: str,
    criteria: list[str],
    question_id: str = "necessity",
) -> tuple[float, float]:
    """Ask a Score question; return (weighted_score, confidence).

    Score is 0-indexed over the ordered criteria list.
    """
    answers = decide(
        state,
        {
            question_id: {
                "type": "score",
                "instructions": instructions,
                "criteria": criteria,
            }
        },
    )
    answer = answers[question_id]
    weighted = float(answer["score"])
    confidence = float(answer.get("confidence") or 0.0)
    print("score_weighted", weighted)
    return weighted, confidence
