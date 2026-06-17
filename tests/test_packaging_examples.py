"""Packaging examples: all five demos run end to end without an infinite loop."""

from __future__ import annotations

import os
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_EX = os.path.join(_ROOT, "examples")


def _run(script, tmp_path):
    proc = subprocess.run(
        [sys.executable, os.path.join(_EX, script),
         "--tester-state-dir", str(tmp_path)],
        capture_output=True, text=True, cwd=_ROOT, timeout=120)
    assert proc.returncode == 0, f"{script}: {proc.stderr}\n{proc.stdout}"
    return proc.stdout


def test_packaging_demo(tmp_path):
    assert "packaging demo" in _run("run_tester_packaging_demo.py",
                                    tmp_path / "pk").lower()


def test_doctor_demo(tmp_path):
    out = _run("run_environment_doctor_demo.py", tmp_path / "doc")
    assert "environment doctor demo" in out.lower()
    assert "missing required command" in out.lower()


def test_clean_machine_demo(tmp_path):
    out = _run("run_clean_machine_check_demo.py", tmp_path / "cm")
    assert "blocker" in out.lower()


def test_manifest_demo(tmp_path):
    out = _run("run_release_manifest_demo.py", tmp_path / "mf")
    assert "calls git  : false" in out.lower()


def test_install_guide_demo(tmp_path):
    out = _run("run_install_guide_demo.py", tmp_path / "ig")
    assert "platform windows" in out.lower()
