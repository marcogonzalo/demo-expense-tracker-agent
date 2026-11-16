"""Base Agent with conversational memory and guarded tool loop."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.llm import LLMError, chat

ToolFn = Callable[..., Any]


class AgentGuardrailError(RuntimeError):
    """Raised when an agent loop guardrail is violated."""


class Agent:
    """Minimal agent loop: messages → optional tools → reply."""

    def __init__(
        self,
        *,
        system_prompt: str = "You are a helpful financial assistant.",
        model: str | None = None,
        max_iterations: int = 8,
        max_tool_calls: int = 12,
        tools: dict[str, ToolFn] | None = None,
    ) -> None:
        self.system_prompt = system_prompt
        self.model = model
        self.max_iterations = max_iterations
        self.max_tool_calls = max_tool_calls
        self.tools = tools or {}
        self.messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt}
        ]
        self.tool_call_count = 0

    def reset(self) -> None:
        """Clear conversation memory (keeps system prompt)."""
        self.messages = [{"role": "system", "content": self.system_prompt}]
        self.tool_call_count = 0

    def call_tool(self, name: str, **kwargs: Any) -> Any:
        """Invoke a registered tool while enforcing the call budget."""
        if name not in self.tools:
            raise AgentGuardrailError(f"Unknown tool: {name}")
        if self.tool_call_count >= self.max_tool_calls:
            raise AgentGuardrailError(
                f"max_tool_calls exceeded ({self.max_tool_calls})"
            )
        self.tool_call_count += 1
        print("tool_name", name)
        return self.tools[name](**kwargs)

    def run(self, user_message: str) -> str:
        """Append a user message and run a bounded chat loop.

        This demo loop does not parse native tool_calls from the model.
        Subclasses / agents call tools explicitly; `run` is for prose turns.
        """
        self.messages.append({"role": "user", "content": user_message})
        iterations = 0
        last_content = ""

        while iterations < self.max_iterations:
            iterations += 1
            print("iterations", iterations)
            try:
                last_content = chat(self.messages, model=self.model)
            except LLMError:
                # Without an API key (or on failure), surface a clear stub.
                last_content = (
                    "LLM unavailable. Configure OPENROUTER_API_KEY to enable "
                    "conversational agent turns."
                )
                self.messages.append({"role": "assistant", "content": last_content})
                return last_content

            self.messages.append({"role": "assistant", "content": last_content})
            # Single-turn chat by default; subclasses may override for tool loops.
            return last_content

        raise AgentGuardrailError(
            f"max_iterations exceeded ({self.max_iterations})"
        )
