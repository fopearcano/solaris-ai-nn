"""Tests for the PilotDeploymentRunner."""

from __future__ import annotations

import json
import time

from solaris_ai_nn.pilot.deployment_runner import PilotDeploymentRunner
from solaris_ai_nn.pilot.pilot_manifest import PilotManifest


def _manifest(tmp_path, profile="simulated", **kw):
    defaults = dict(profile=profile, operator="tester",
                    state_dir=str(tmp_path / "state"),
                    artifact_dir=str(tmp_path / "pilots"),
                    max_steps=60, notes="bounded test pilot")
    defaults.update(kw)
    return PilotManifest(**defaults)


def _runner(tmp_path, manifest, **kw):
    return PilotDeploymentRunner(manifest=manifest,
                                 approved_output_roots=[str(tmp_path)], **kw)


def test_simulated_pilot_runs_bounded(tmp_path):
    start = time.perf_counter()
    runner = _runner(tmp_path, _manifest(tmp_path))
    runner.acknowledge_risks()
    snapshot = runner.run()
    assert time.perf_counter() - start < 120.0  # no infinite loop
    assert not snapshot["refused"]
    entry = snapshot["registry_entry"]
    assert entry["status"] == "completed"
    assert entry["final_recommendation"]
    for name in ("pilot_manifest.json", "safety_contract.json",
                 "readiness_report.json", "pilot_report.json",
                 "pilot_report.md", "input_summary.json", "artifacts.json"):
        assert (runner.pilot_dir / name).exists(), name


def test_read_only_stream_pilot_runs_bounded(tmp_path):
    src = tmp_path / "events.jsonl"
    src.write_text("\n".join(
        json.dumps({"source": "lab", "payload": f"e{i}", "intensity": 0.5})
        for i in range(20)))
    before = src.read_bytes()
    runner = _runner(tmp_path, _manifest(tmp_path, profile="read_only_stream",
                                         input_sources=[str(src)]))
    runner.acknowledge_risks()
    snapshot = runner.run()
    assert not snapshot["refused"]
    assert snapshot["registry_entry"]["status"] == "completed"
    summary = json.loads(
        (runner.pilot_dir / "input_summary.json").read_text())
    ingestion = summary["sensors"][0]["source"]["ingestion"]
    assert ingestion["events_accepted"] == 20
    assert src.read_bytes() == before  # the input was only read


def test_unsafe_pilot_refused(tmp_path):
    manifest = _manifest(tmp_path, profile="read_only_stream",
                         input_sources=[str(tmp_path / "missing.jsonl")])
    runner = _runner(tmp_path, manifest)
    snapshot = runner.run()
    assert snapshot["refused"]
    assert snapshot["refusal_reasons"]
    assert snapshot["registry_entry"]["status"] == "refused"
    assert runner.supervisor is None  # nothing was ever started
    assert not (runner.pilot_dir / "pilot_report.md").exists()


def test_unacknowledged_medium_risk_refused_by_governance(tmp_path):
    # Simulated profile carries the medium embodiment risk; without the
    # operator acknowledging it, the supervisor's governance gate refuses.
    runner = _runner(tmp_path, _manifest(tmp_path))
    snapshot = runner.run()
    assert snapshot["refused"]
    assert any("acknowledgement" in r for r in snapshot["refusal_reasons"])


def test_stop_honoured_mid_pilot(tmp_path):
    manifest = _manifest(tmp_path, max_steps=200)
    runner = _runner(tmp_path, manifest)
    runner.acknowledge_risks()
    runner.prepare()
    original = runner.supervisor._supervise

    def stop_after_first(*args, **kw):
        original(*args, **kw)
        runner.stop("test stop")

    runner.supervisor._supervise = stop_after_first
    runner.run()
    assert runner.supervisor._segments_run < 8  # stopped early


def test_pilot_summary_keys(tmp_path):
    runner = _runner(tmp_path, _manifest(tmp_path))
    runner.acknowledge_risks()
    runner.run()
    summary = runner.pilot_summary()
    for key in ("pilot_mode_active", "pilot_profile",
                "pilot_readiness_status", "input_source_count",
                "stream_ingestion_count", "pilot_safety_status",
                "pilot_incident_count", "pilot_recommendation",
                "pilot_report_path"):
        assert key in summary, key
    assert summary["pilot_profile"] == "simulated"
    assert summary["pilot_safety_status"] == "safe"
