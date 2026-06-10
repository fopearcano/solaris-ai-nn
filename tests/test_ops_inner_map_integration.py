"""Tests for operations in the Inner MAP."""

from __future__ import annotations

from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph
from solaris_ai_nn.ops.run_manifest import OperationalRunManifest
from solaris_ai_nn.ops.run_registry import RunRegistry
from solaris_ai_nn.ops.supervisor import OperationalSupervisor

OPS_NODES = {"operational_supervisor", "health_monitor", "watchdog",
             "resource_budget", "safe_shutdown_manager", "incident_log",
             "run_registry", "artifact_rotation_policy",
             "local_status_server"}


def test_inner_map_includes_operational_health(tmp_path):
    manifest = OperationalRunManifest(
        max_steps=40, healthcheck_interval_steps=20,
        state_dir=str(tmp_path / "state"), artifact_dir=str(tmp_path / "ops"))
    sup = OperationalSupervisor(manifest=manifest,
                                registry=RunRegistry(tmp_path / "reg.json"))
    sup.run()
    model = InnerMapObserver(bridge=sup._last_runner.bridge,
                             operations=sup).update()
    ops = model.operations
    assert ops is not None
    assert ops["run_mode"] == "bounded"
    assert ops["health_level"] in ("ok", "warning", "critical", "unknown")
    assert ops["graceful_shutdown_requested"] is True
    assert ops["local_status_server"]["enabled"] is False
    assert "operations" in model.to_dict()


def test_state_graph_includes_ops_nodes():
    g = build_default_state_graph()
    assert OPS_NODES <= set(g.nodes)
    labels = {(s, d): l for s, d, l in g.edges}
    assert ("health_monitor", "watchdog") in labels
    assert labels[("watchdog", "safe_shutdown_manager")] == \
        "can request safe shutdown"
    assert ("incident_log", "inner_map") in labels
    assert "operational_supervisor" in g.to_mermaid()
