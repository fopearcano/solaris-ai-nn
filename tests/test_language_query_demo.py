"""Tests for the language query demo (deterministic, no LLM)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXAMPLE = REPO / "examples" / "run_language_query_demo.py"


def test_deterministic_queries_return_answers(tmp_path):
    proc = subprocess.run(
        [sys.executable, str(EXAMPLE), "--steps", "60",
         "--state-dir", str(tmp_path / "q")],
        capture_output=True, text=True, timeout=120, cwd=str(REPO),
    )
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    assert "what happened last?" in out
    assert "what habit is strongest?" in out
    assert "[ok ]" in out  # at least some queries answered
    assert "no LLM" in out


def test_no_external_llm_imports():
    """Static check: the language package never imports LLM/network stacks."""
    package = REPO / "src" / "solaris_ai_nn" / "language"
    source = "".join(p.read_text() for p in package.glob("*.py"))
    for forbidden in ("transformers", "langchain", "openai", "anthropic",
                      "requests", "urllib", "torch", "tensorflow", "socket"):
        assert forbidden not in source, forbidden
