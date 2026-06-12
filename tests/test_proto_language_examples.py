"""Subprocess tests for the proto-language examples."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXAMPLES = REPO / "examples"


def _run(script, *args, timeout=300):
    start = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, str(EXAMPLES / script), *args],
        capture_output=True, text=True, timeout=timeout, cwd=str(REPO))
    assert time.perf_counter() - start < timeout, f"{script}: no infinite loop"
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def test_proto_language_demo_runs(tmp_path):
    out = _run("run_proto_language_demo.py", "--steps", "100",
               "--state-dir", str(tmp_path / "s"))
    assert "internal signs, not human language" in out
    assert "symbols emerged:" in out
    assert "first_proto_symbol" in out
    assert "claim guard safe: True" in out
    assert "no teacher, no LLM" in out
    assert (tmp_path / "s" / "proto_symbols.json").exists()


def test_symbol_emergence_demo_runs(tmp_path):
    out = _run("run_symbol_emergence_demo.py",
               "--state-dir", str(tmp_path / "s"), timeout=60)
    assert "repetition earns a name" in out
    assert "the one-off pattern earned nothing" in out
    assert "rejected: True" in out  # unmarked counterfactual
    assert "stable=True" in out
    assert (tmp_path / "s" / "proto_symbols.jsonl").exists()


def test_proto_utterance_demo_runs(tmp_path):
    out = _run("run_proto_utterance_demo.py",
               "--state-dir", str(tmp_path / "s"), timeout=60)
    assert "structure, not speech" in out
    assert "proto-utterance (memory):" in out
    assert "debug translation:" in out
    assert "not human language" in out
    assert "safety: ok" in out


def test_symbol_prediction_demo_runs(tmp_path):
    out = _run("run_symbol_prediction_demo.py", timeout=60)
    assert "structured sequences" in out
    assert "improved" in out
    assert "shuffled noise" in out
    assert "honest" in out  # honest-reporting wording present


def test_proto_language_safety_demo_runs(tmp_path):
    out = _run("run_proto_language_safety_demo.py",
               "--state-dir", str(tmp_path / "s"), timeout=60)
    assert "blocked: True" in out
    assert "unmarked counterfactual rejected: True" in out
    assert "claim guard safe: True" in out
    assert "no execution path" in out
