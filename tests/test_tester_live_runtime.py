"""Tester live runtime: bounded, writes templates, validates samples, no control."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.tester_live_readonly import TesterLiveReadOnlyRuntime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_live_helpers import approve_governance  # noqa: E402


def test_bounded_runtime(tmp_path):
    rt = TesterLiveReadOnlyRuntime(
        state_dir=str(tmp_path / "live"),
        tester_state_dir=str(tmp_path / "tester"), max_runtime_s=0)
    assert rt.run()["refused"] is True


def test_writes_templates(tmp_path):
    live = str(tmp_path / "live")
    rt = TesterLiveReadOnlyRuntime(
        state_dir=live, tester_state_dir=str(tmp_path / "tester"),
        profile="tester_live_init_only_v0")
    rt.run()
    assert os.path.isfile(os.path.join(
        live, "governance", "LIVE_READONLY_GOVERNANCE.json"))
    assert os.path.isfile(os.path.join(live, "feeders", "FEEDER_REGISTRY.json"))


def test_validates_samples(tmp_path):
    rt = TesterLiveReadOnlyRuntime(
        state_dir=str(tmp_path / "live"),
        tester_state_dir=str(tmp_path / "tester"))
    rt.run()
    assert rt.sample_validation["safe"]["all_accepted"]
    assert rt.sample_validation["unsafe"]["all_quarantined"]


def test_runs_local_birth_membrane_observation(tmp_path):
    live = str(tmp_path / "live")
    TesterLiveReadOnlyRuntime(
        state_dir=live, tester_state_dir=str(tmp_path / "tester"),
        profile="tester_live_init_only_v0").run()
    approve_governance(live)
    rt = TesterLiveReadOnlyRuntime(
        state_dir=live, tester_state_dir=str(tmp_path / "tester"),
        write_templates=False, copy_safe_samples_to_inbox=True,
        run_birth=True, run_membrane=True, run_integration=True,
        run_observation=True)
    rt.run()
    assert rt.membrane_status.get("membrane_impression_count", 0) >= 1
    assert rt.observation_status.get("live_observation_enabled") is True


def test_does_not_start_feeders(tmp_path):
    rt = TesterLiveReadOnlyRuntime(
        state_dir=str(tmp_path / "live"),
        tester_state_dir=str(tmp_path / "tester"))
    rt.run()
    st = rt.tester_live_status()
    assert st["starts_feeders"] is False
    assert st["controls_hardware"] is False
    assert st["accesses_network"] is False
    assert st["runs_git"] is False
    assert st["publishes"] is False
    assert st["trains_on_feedback"] is False


def test_doctor_runs(tmp_path):
    rt = TesterLiveReadOnlyRuntime(
        state_dir=str(tmp_path / "live"),
        tester_state_dir=str(tmp_path / "tester"))
    doc = rt.run_doctor()
    assert "overall_status" in doc
