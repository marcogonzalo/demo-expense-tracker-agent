"""TDD: agent loop execution guardrails."""

from __future__ import annotations

import unittest

from src.agent import Agent, AgentGuardrailError


class TestAgentGuardrails(unittest.TestCase):
    def test_max_tool_calls_enforced(self) -> None:
        calls = {"n": 0}

        def ping() -> str:
            calls["n"] += 1
            return "pong"

        agent = Agent(max_tool_calls=2, tools={"ping": ping})
        self.assertEqual(agent.call_tool("ping"), "pong")
        self.assertEqual(agent.call_tool("ping"), "pong")
        with self.assertRaises(AgentGuardrailError):
            agent.call_tool("ping")

    def test_unknown_tool_rejected(self) -> None:
        agent = Agent(tools={})
        with self.assertRaises(AgentGuardrailError):
            agent.call_tool("missing")

    def test_max_iterations_constant_present(self) -> None:
        agent = Agent(max_iterations=3)
        self.assertEqual(agent.max_iterations, 3)


if __name__ == "__main__":
    unittest.main()
