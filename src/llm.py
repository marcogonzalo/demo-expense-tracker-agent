"""Lightweight OpenRouter chat client for Agent Loop / Fase 4."""

from __future__ import annotations

from typing import Any

import httpx

from src.config import CHAT_MODEL, OPENROUTER_API_KEY, OPENROUTER_BASE_URL


class LLMError(RuntimeError):
    """Raised when the chat completion request fails."""


def chat(
    messages: list[dict[str, Any]],
    *,
    model: str | None = None,
    temperature: float = 0.2,
    timeout: float = 90.0,
) -> str:
    """Send a chat completion and return the assistant text content."""
    if not OPENROUTER_API_KEY:
        raise LLMError("OPENROUTER_API_KEY is not set")

    selected_model = model or CHAT_MODEL
    print("selected_model", selected_model)

    url = f"{OPENROUTER_BASE_URL.rstrip('/')}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/4Geeks/demo-expense-tracker-agent",
        "X-Title": "Demo Expense Tracker Agent",
    }
    payload = {
        "model": selected_model,
        "messages": messages,
        "temperature": temperature,
    }

    with httpx.Client(timeout=timeout) as client:
        response = client.post(url, headers=headers, json=payload)

    if response.status_code >= 400:
        raise LLMError(f"OpenRouter chat failed ({response.status_code}): {response.text}")

    data = response.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMError(f"Unexpected chat response shape: {data}") from exc

    return content or ""
