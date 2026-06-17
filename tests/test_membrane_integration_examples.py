"""Membrane integration example scripts run end to end without error."""

from __future__ import annotations

import os
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_EX = os.path.join(_ROOT, "examples")


def _run(script, state_dir):
    proc = subprocess.run(
        [sys.executable, os.path.join(_EX, script),
         "--state-dir", state_dir],
        capture_output=True, text=True, cwd=_ROOT)
    assert proc.returncode == 0, f"{script}: {proc.stderr}\n{proc.stdout}"
    return proc.stdout


def test_integration_demo(tmp_path):
    out = _run("run_membrane_integration_demo.py",
               os.path.join(str(tmp_path), "integ"))
    assert "ancestry" in out.lower()


def test_bypass_demo(tmp_path):
    out = _run("run_membrane_bypass_demo.py",
               os.path.join(str(tmp_path), "bypass"))
    assert "bypass" in out.lower()


def test_ancestry_demo(tmp_path):
    out = _run("run_membrane_ancestry_demo.py",
               os.path.join(str(tmp_path), "anc"))
    assert "ancestry" in out.lower()


def test_contracts_demo(tmp_path):
    out = _run("run_membrane_contracts_demo.py",
               os.path.join(str(tmp_path), "contracts"))
    assert "contract" in out.lower()


def test_pipeline_audit_demo(tmp_path):
    out = _run("run_membrane_pipeline_audit_demo.py",
               os.path.join(str(tmp_path), "audit"))
    assert "pipeline" in out.lower() or "stage" in out.lower()
