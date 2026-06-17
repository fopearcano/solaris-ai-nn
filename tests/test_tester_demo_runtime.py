"""Tester demo runtime: bounded fixture-only, reports + bundle, no external control."""

from __future__ import annotations

import os

from solaris_ai_nn.tester_fixture_spine import TesterFixtureDemoRuntime


def test_bounded_fixture_only_runtime(tmp_path):
    rt = TesterFixtureDemoRuntime(state_dir=str(tmp_path))
    result = rt.run()
    assert result["refused"] is False
    assert result["blocked"] is False
    assert result["fixture_event_count"] >= 14
    assert result["membrane_impression_count"] >= 1


def test_unbounded_runtime_refused(tmp_path):
    rt = TesterFixtureDemoRuntime(state_dir=str(tmp_path), max_runtime_s=0)
    assert rt.run()["refused"] is True


def test_reports_generated(tmp_path):
    rt = TesterFixtureDemoRuntime(state_dir=str(tmp_path))
    rt.run()
    assert os.path.isfile(rt.reports["markdown"])
    assert os.path.isfile(rt.reports["summary"])
    reports_dir = os.path.join(str(tmp_path), "reports")
    assert os.path.isfile(os.path.join(
        reports_dir, "TESTER_FIXTURE_SPINE_REPORT.md"))


def test_bundle_generated(tmp_path):
    rt = TesterFixtureDemoRuntime(state_dir=str(tmp_path))
    rt.run()
    assert os.path.isdir(rt.bundle.manifest.bundle_dir)
    assert os.path.isfile(os.path.join(
        rt.bundle.manifest.bundle_dir, "BUNDLE_MANIFEST.json"))


def test_no_external_control(tmp_path):
    rt = TesterFixtureDemoRuntime(state_dir=str(tmp_path))
    rt.run()
    st = rt.tester_status()
    assert st["starts_feeders"] is False
    assert st["controls_hardware"] is False
    assert st["accesses_network"] is False
    assert st["runs_git"] is False
    assert st["publishes"] is False
    assert st["trains_on_feedback"] is False
    assert st["requires_live_data"] is False


def test_previous_runs_not_deleted(tmp_path):
    rt1 = TesterFixtureDemoRuntime(state_dir=str(tmp_path))
    rt1.run()
    rt2 = TesterFixtureDemoRuntime(state_dir=str(tmp_path))
    rt2.run()
    runs = os.listdir(os.path.join(str(tmp_path), "runs"))
    assert len(runs) == 2


def test_doctor_requires_no_live_data(tmp_path):
    rt = TesterFixtureDemoRuntime(state_dir=str(tmp_path))
    doc = rt.run_doctor()
    assert doc["requires_live_data"] is False
    assert doc["requires_governance"] is False
    assert doc["passed"] is True
