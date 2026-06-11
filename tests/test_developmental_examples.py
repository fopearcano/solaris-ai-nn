"""Subprocess tests for the developmental examples."""

from __future__ import annotations

import json
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


def test_short_demo_runs(tmp_path):
    out = _run("run_developmental_short_demo.py", "--steps", "100",
               "--state-dir", str(tmp_path / "s"))
    assert "simulated time, bounded" in out
    assert "developmental age:" in out
    assert "current epoch:" in out
    assert "claim guard safe: True" in out
    assert "no teacher" in out
    assert (tmp_path / "s" / "developmental_state.json").exists()
    assert (tmp_path / "s" / "fossil_memory.jsonl").exists()


def test_memory_layer_demo_runs(tmp_path):
    out = _run("run_memory_layer_demo.py",
               "--state-dir", str(tmp_path / "s"), timeout=60)
    assert "raw events never grow forever" in out
    assert "compression report:" in out
    assert "preserved important:" in out
    assert "never silently destroys evidence" in out
    assert (tmp_path / "s" / "fossil_memory.jsonl").exists()


def test_milestone_demo_runs(tmp_path):
    out = _run("run_milestone_demo.py",
               "--state-dir", str(tmp_path / "s"), timeout=60)
    assert "first_stable_habit" in out
    assert "first_mysterium_spike" in out
    assert "first_successful_consolidation" in out
    assert "each first fires once" in out
    assert "not awareness" in out


def test_drift_growth_demo_runs(tmp_path):
    out = _run("run_drift_growth_demo.py",
               "--state-dir", str(tmp_path / "s"), timeout=60)
    assert "accumulation" in out
    assert "stagnation" in out
    assert "fast_warning" in out
    assert "phase-transition candidates:" in out
    assert "never assumed" in out


def test_month_scale_plan_generates_only_a_plan(tmp_path):
    start = time.perf_counter()
    out = _run("run_month_scale_plan.py",
               "--output-dir", str(tmp_path / "plan"), timeout=60)
    # A plan generator, not a long run: it finishes fast.
    assert time.perf_counter() - start < 60
    assert "no run is started" in out
    assert "governance checklist" in out
    assert "refused as designed" in out
    plan_path = tmp_path / "plan" / "month_scale_plan.json"
    assert plan_path.exists()
    plan = json.loads(plan_path.read_text())
    assert plan["plan"]["target_runtime_days"] == 30
    assert any(not item["satisfied"] for item in plan["checklist"])
