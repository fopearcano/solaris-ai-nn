"""Research baseline examples run bounded (no infinite loop) with expected output."""

from __future__ import annotations

import os
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run(example, state_dir, timeout=120):
    path = os.path.join(_ROOT, "examples", example)
    proc = subprocess.run(
        [sys.executable, path, "--state-dir", state_dir],
        capture_output=True, text=True, timeout=timeout, cwd=_ROOT)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def test_research_baseline_demo_runs(tmp_path):
    out = _run("run_research_baseline_snapshot_demo.py", str(tmp_path / "b"))
    assert "Research baseline demo" in out
    assert "is git tag            : False" in out


def test_repro_bundle_demo_runs(tmp_path):
    out = _run("run_repro_bundle_demo.py", str(tmp_path / "r"))
    assert "Repro bundle demo" in out
    assert "fetches remote" in out


def test_capability_map_demo_runs(tmp_path):
    out = _run("run_capability_map_demo.py", str(tmp_path / "c"))
    assert "Capability map demo" in out
    assert "validated" in out


def test_limitation_registry_demo_runs(tmp_path):
    out = _run("run_limitation_registry_demo.py", str(tmp_path / "l"))
    assert "Limitation registry demo" in out
    assert "blocks validation     : True" in out


def test_next_cycle_roadmap_demo_runs(tmp_path):
    out = _run("run_next_cycle_roadmap_demo.py", str(tmp_path / "rm"))
    assert "Next-cycle roadmap demo" in out
    assert "run_mini_soak" in out
