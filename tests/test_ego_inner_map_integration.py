"""Tests for the ego layer inside the Inner MAP."""

from __future__ import annotations

from solaris_ai_nn.ego.self_model import SelfModel
from solaris_ai_nn.inner_map.model import InnerMapModel
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph


def test_inner_map_includes_ego_state(tmp_path):
    model = SelfModel(state_dir=tmp_path)
    model.update({"run_id": "r1", "session_id": "s1"})
    inner = InnerMapObserver(ego=model).update()
    assert inner.ego is not None
    for key in ("enabled", "identity_continuity", "perspective",
                "boundary_violation_count", "active_boundaries",
                "classification_counts", "action_authority",
                "self_model_confidence", "identity_warnings",
                "narrative_trace_path", "self_report_path"):
        assert key in inner.ego, key
    assert inner.ego["enabled"] is True
    assert inner.ego["active_boundaries"] == 16
    clone = InnerMapModel.from_dict(inner.to_dict())
    assert clone.ego["perspective"] == "internal_runtime"


def test_ego_absent_when_disabled():
    assert InnerMapObserver().update().ego is None


def test_observer_picks_ego_from_runner(tmp_path):
    from solaris_ai_nn.runtime.continuous_runner import ContinuousRunner

    runner = ContinuousRunner(state_dir=str(tmp_path / "s"), max_steps=60,
                              seed=3, enable_ego=True,
                              ego_update_interval_steps=20)
    runner.run()
    inner = runner.observer.update()
    assert inner.ego is not None  # via runner duck-typing
    assert inner.ego["identity_continuity"] == 1.0


def test_state_graph_includes_ego_nodes():
    graph = build_default_state_graph()
    for node in ("self_model", "identity_state", "boundary_registry",
                 "dimensional_comparator", "ownership_attributor",
                 "ego_continuity_monitor", "body_schema",
                 "perspective_tracker", "narrative_trace",
                 "ego_safety_validator"):
        assert node in graph.nodes, node
    edges = {(src, dst) for src, dst, _ in graph.edges}
    assert ("telemetry", "identity_state") in edges
    assert ("governance_policy", "boundary_registry") in edges
    assert ("solaris_nn_sidecar", "perspective_tracker") in edges
    assert ("sleep_wake_controller", "boundary_registry") in edges
    assert ("action_arbitrator", "boundary_registry") in edges
    assert ("world_model_builder", "self_model") in edges
    assert ("self_model", "inner_map") in edges
    assert "self_model" in graph.to_mermaid()
