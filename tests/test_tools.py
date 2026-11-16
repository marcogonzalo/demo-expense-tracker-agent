"""TDD: WORKDIR path confinement / traversal guardrails."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.tools import PathTraversalError, read_expenses_csv, resolve_under_workdir


class TestWorkdirGuardrails(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.workdir = Path(self.tmp.name).resolve()
        (self.workdir / "expenses_log.csv").write_text(
            "date,concept,amount\n2026-06-01,Nómina,+1350.00\n",
            encoding="utf-8",
        )
        self.workdir_patch = mock.patch("src.tools.WORKDIR", self.workdir)
        self.workdir_patch.start()

    def tearDown(self) -> None:
        self.workdir_patch.stop()
        self.tmp.cleanup()

    def test_relative_file_inside_workdir_ok(self) -> None:
        path = resolve_under_workdir("expenses_log.csv")
        self.assertEqual(path, self.workdir / "expenses_log.csv")

    def test_dotdot_escape_rejected(self) -> None:
        with self.assertRaises(PathTraversalError):
            resolve_under_workdir("../etc/passwd")

    def test_nested_dotdot_rejected(self) -> None:
        with self.assertRaises(PathTraversalError):
            resolve_under_workdir("../../etc/passwd")

    def test_sibling_escape_via_dotdot_rejected(self) -> None:
        outside = (self.workdir / ".." / "outside.txt").resolve()
        outside.write_text("nope", encoding="utf-8")
        with self.assertRaises(PathTraversalError):
            resolve_under_workdir("../outside.txt")

    def test_absolute_external_path_rejected(self) -> None:
        with self.assertRaises(PathTraversalError):
            resolve_under_workdir("/etc/passwd")

    def test_read_expenses_csv_parses_rows(self) -> None:
        rows = read_expenses_csv("expenses_log.csv")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["concept"], "Nómina")
        self.assertEqual(rows[0]["amount"], 1350.0)


if __name__ == "__main__":
    unittest.main()
