"""Review assimilation examples run end to end without hanging."""

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


def test_review_assimilation_demo_runs(tmp_path):
    out = _run("run_review_assimilation_demo.py", tmp_path)
    assert "Review assimilation demo" in out
    assert "trains model          : False" in out


def test_objection_classifier_demo_runs(tmp_path):
    out = _run("run_objection_classifier_demo.py", tmp_path)
    assert "BLOCKS" in out


def test_reproduction_outcome_demo_runs(tmp_path):
    out = _run("run_reproduction_outcome_demo.py", tmp_path)
    assert "project limitation" in out


def test_claim_revision_demo_runs(tmp_path):
    out = _run("run_claim_revision_demo.py", tmp_path)
    assert "edits_registry=False" in out


def test_review_driven_experiment_demo_runs(tmp_path):
    out = _run("run_review_driven_experiment_demo.py", tmp_path)
    assert "executed=False" in out
    assert "run_passive_parser_control" in out
