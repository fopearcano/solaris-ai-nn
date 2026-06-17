"""Safety freeze runtime: bounded, reports, no network/Git/shell/publish, read-only."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.tester_safety_freeze import TesterSafetyFreezeRuntime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_safety_freeze_helpers import run_freeze  # noqa: E402


def test_bounded_runtime(tmp_path):
    rt = TesterSafetyFreezeRuntime(tester_state_dir=str(tmp_path),
                                   max_runtime_s=0)
    assert rt.run()["refused"] is True


def test_reports_generated(tmp_path):
    rt = run_freeze(tmp_path)
    reports = os.path.join(str(tmp_path), "safety_freeze", "reports")
    assert os.path.isfile(os.path.join(reports,
                                       "TESTER_SAFETY_FREEZE_REPORT.md"))


def test_no_network_git_shell_publish(tmp_path):
    rt = run_freeze(tmp_path)
    snap = rt.safety.snapshot()
    assert snap["can_access_network"] is False
    assert snap["can_run_git"] is False
    assert snap["can_run_shell"] is False
    assert snap["can_publish"] is False
    assert snap["can_create_releases"] is False


def test_no_behavior_modification(tmp_path):
    rt = run_freeze(tmp_path)
    st = rt.safety_freeze_status()
    assert st["local_only"] is True
    assert st["publishes"] is False


def test_doctor(tmp_path):
    rt = TesterSafetyFreezeRuntime(tester_state_dir=str(tmp_path))
    doc = rt.run_doctor()
    assert doc["report_gate_only"] is True
