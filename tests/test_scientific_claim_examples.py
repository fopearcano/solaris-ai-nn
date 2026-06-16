"""Scientific claim examples run end to end without hanging."""

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


def test_scientific_claims_demo_runs(tmp_path):
    out = _run("run_scientific_claims_demo.py", tmp_path)
    assert "Scientific claims demo" in out


def test_theory_ledger_demo_runs(tmp_path):
    out = _run("run_theory_ledger_demo.py", tmp_path)
    assert "Theory ledger demo" in out


def test_counterevidence_demo_runs(tmp_path):
    out = _run("run_counterevidence_demo.py", tmp_path)
    assert "Counterevidence demo" in out


def test_publication_dossier_demo_runs(tmp_path):
    out = _run("run_publication_dossier_demo.py", tmp_path)
    assert "blocked_by_forbidden_claims" in out


def test_safe_abstract_demo_runs(tmp_path):
    out = _run("run_safe_abstract_demo.py", tmp_path)
    assert "Safe abstract demo" in out
    assert "makes no claim of consciousness" in out
