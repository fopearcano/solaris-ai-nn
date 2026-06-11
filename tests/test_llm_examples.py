"""Subprocess tests for the LLM adapter examples."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXAMPLES = REPO / "examples"


def _run(script, *args, timeout=120):
    start = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, str(EXAMPLES / script), *args],
        capture_output=True, text=True, timeout=timeout, cwd=str(REPO))
    assert time.perf_counter() - start < timeout, f"{script}: no infinite loop"
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def test_mock_paraphrase_demo_runs(tmp_path):
    out = _run("run_llm_mock_paraphrase_demo.py",
               "--state-dir", str(tmp_path / "s"))
    assert "translator, not authority" in out
    assert "deterministic response:" in out
    assert "In plain terms:" in out
    assert "fallback to deterministic: True" in out
    assert "hashes only" in out


def test_classification_assist_demo_runs(tmp_path):
    out = _run("run_llm_classification_assist_demo.py",
               "--state-dir", str(tmp_path / "s"))
    assert "LLM suggestion: kind=state_query" in out
    assert "resolved (safely): state_query" in out
    assert "unsafe cannot be" in out
    assert "safer class wins" in out


def test_report_polish_demo_runs(tmp_path):
    out = _run("run_llm_report_polish_demo.py",
               "--state-dir", str(tmp_path / "s"))
    assert "polish accepted: True" in out
    assert "claim guard re-scan of polished file: True" in out
    assert "accepted: False" in out  # the forced-unsafe attempt
    assert (tmp_path / "s" / "session_report.polished.md").exists()
    assert (tmp_path / "s" / "llm_audit.jsonl").exists()


def test_endpoint_check_demo_runs_without_real_endpoint(tmp_path):
    out = _run("run_local_llm_endpoint_check.py",
               "--endpoint-url", "http://127.0.0.1:11434")
    assert "safety decision: ALLOWED" in out
    assert "no request attempted" in out
    remote = _run("run_local_llm_endpoint_check.py",
                  "--endpoint-url", "http://example.com:11434")
    assert "safety decision: REFUSED" in remote
    # --try-request against a dead local port refuses gracefully.
    dead = _run("run_local_llm_endpoint_check.py",
                "--endpoint-url", "http://127.0.0.1:9",
                "--try-request")
    assert "refused gracefully" in dead
