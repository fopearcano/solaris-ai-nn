"""Independent review examples run end to end without hanging."""

from __future__ import annotations

import os
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run(script, tmp_path):
    path = os.path.join(_ROOT, "examples", script)
    result = subprocess.run(
        [sys.executable, path, "--state-dir", str(tmp_path)],
        capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_independent_review_demo_runs(tmp_path):
    out = _run("run_independent_review_demo.py", tmp_path)
    assert "Independent review demo" in out
    assert "published / uploaded  : False / False" in out


def test_artifact_sanitizer_demo_runs(tmp_path):
    out = _run("run_artifact_sanitizer_demo.py", tmp_path)
    assert "blocks readiness: True" in out


def test_reproducibility_challenge_demo_runs(tmp_path):
    out = _run("run_reproducibility_challenge_demo.py", tmp_path)
    assert "unavailable" in out


def test_adversarial_review_demo_runs(tmp_path):
    out = _run("run_adversarial_review_demo.py", tmp_path)
    assert "STRONG" in out


def test_response_ledger_demo_runs(tmp_path):
    out = _run("run_response_ledger_demo.py", tmp_path)
    assert "accepted limitations : 1" in out
    assert "unresolved           : 1" in out
