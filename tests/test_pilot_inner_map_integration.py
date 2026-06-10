"""Tests for pilot state inside the Inner MAP."""

from __future__ import annotations

from solaris_ai_nn.inner_map.model import InnerMapModel
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph
from solaris_ai_nn.pilot.deployment_runner import PilotDeploymentRunner
from solaris_ai_nn.pilot.pilot_manifest import PilotManifest


def test_inner_map_includes_pilot_state_from_dict():
    observer = InnerMapObserver(pilot={
        "pilot_mode_active": True, "pilot_profile": "simulated",
        "pilot_readiness_status": "ready", "input_source_count": 0,
        "stream_ingestion_count": 0, "pilot_safety_status": "safe",
        "pilot_incident_count": 0, "pilot_recommendation": None,
        "pilot_report_path": None})
    model = observer.update()
    assert model.pilot["pilot_profile"] == "simulated"
    assert model.to_dict()["pilot"]["pilot_safety_status"] == "safe"
    # Round-trips through serialization.
    clone = InnerMapModel.from_dict(model.to_dict())
    assert clone.pilot["pilot_readiness_status"] == "ready"


def test_inner_map_observes_real_pilot(tmp_path):
    manifest = PilotManifest(profile="simulated", operator="tester",
                             state_dir=str(tmp_path / "state"),
                             artifact_dir=str(tmp_path / "pilots"),
                             max_steps=60, notes="inner map test")
    runner = PilotDeploymentRunner(manifest=manifest,
                                   approved_output_roots=[str(tmp_path)])
    runner.acknowledge_risks()
    runner.run()
    model = InnerMapObserver(pilot=runner).update()
    assert model.pilot["pilot_profile"] == "simulated"
    assert model.pilot["pilot_safety_status"] == "safe"
    assert model.pilot["pilot_recommendation"]
    # The deployment runner also persisted a pilot-aware Inner MAP.
    assert (runner.pilot_dir / "pilot_inner_map.json").exists()


def test_pilot_absent_when_no_pilot():
    model = InnerMapObserver().update()
    assert model.pilot is None


def test_state_graph_includes_pilot_nodes():
    graph = build_default_state_graph()
    for node in ("pilot_profile", "pilot_manifest", "pilot_safety_validator",
                 "pilot_deployment_runner", "pilot_readiness_report",
                 "pilot_report", "read_only_stream_ingestor",
                 "stream_sensor"):
        assert node in graph.nodes, node
    edges = {(src, dst) for src, dst, _ in graph.edges}
    assert ("pilot_manifest", "governance_policy") in edges
    assert ("pilot_safety_validator", "pilot_deployment_runner") in edges
    assert ("stream_sensor", "bridge") in edges
    assert ("operational_supervisor", "pilot_deployment_runner") in edges
    assert ("evaluation_score", "pilot_report") in edges
    assert ("pilot_report", "inner_map") in edges
    # Renders still work with the new nodes.
    assert "pilot_deployment_runner" in graph.to_mermaid()
    assert "pilot_report" in graph.to_dot()
