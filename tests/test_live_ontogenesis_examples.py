"""Live ontogenesis examples run end to end without hanging."""

from __future__ import annotations

import os
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run(script, tmp_path, extra=None):
    path = os.path.join(_ROOT, "examples", script)
    cmd = [sys.executable, path, "--state-dir", str(tmp_path)]
    cmd += extra or []
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_ontogenesis_demo_runs(tmp_path):
    out = _run("run_live_ontogenesis_demo.py", tmp_path)
    assert "First live ontogenesis demo" in out
    assert "semiogenesis/action : False / False" in out


def test_feature_extraction_demo_runs(tmp_path):
    out = _run("run_live_feature_extraction_demo.py", tmp_path)
    assert "Live feature extraction demo" in out
    assert "debug gloss" in out


def test_proto_concept_candidate_demo_runs(tmp_path):
    out = _run("run_live_proto_concept_candidate_demo.py", tmp_path)
    assert "Live proto-concept candidate demo" in out
    assert "candidates" in out


def test_contamination_filter_demo_runs(tmp_path):
    out = _run("run_live_contamination_filter_demo.py", tmp_path)
    assert "Live contamination filter demo" in out
    assert "operator_pulse_dominance" in out


def test_concept_birth_gate_demo_runs(tmp_path):
    out = _run("run_live_concept_birth_gate_demo.py", tmp_path)
    assert "Live concept birth gate demo" in out
    assert "distinct gate statuses observed" in out
