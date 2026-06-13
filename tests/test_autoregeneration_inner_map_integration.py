"""Integration: auto-regeneration state in Inner MAP + state graph."""

from __future__ import annotations

from solaris_ai_nn.autoregeneration import AutoRegenerationEngine, RepairPolicy
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph


def _engine(tmp_path):
    engine = AutoRegenerationEngine(
        state_dir=tmp_path, policy=RepairPolicy(mode="safe_auto_repair"))
    engine.tick({"memory": {"over_budget": ["hot"]},
                 "mysterium_pressure": 0.97, "state_dir": str(tmp_path)})
    return engine


def test_inner_map_includes_autoregeneration(tmp_path):
    model = InnerMapObserver(autoregeneration=_engine(tmp_path)).update()
    assert model.autoregeneration is not None
    assert model.autoregeneration["enabled"] is True
    assert model.autoregeneration["authority"] is False
    assert "repair_policy_mode" in model.autoregeneration


def test_inner_map_finds_engine_on_developmental(tmp_path):
    engine = _engine(tmp_path)

    class FakeDevelopmental:
        def __init__(self, e):
            self.autoregeneration = e

        def summary(self):
            return {"enabled": True}

    model = InnerMapObserver(
        developmental=FakeDevelopmental(engine)).update()
    assert model.autoregeneration is not None


def test_state_graph_has_autoregeneration_nodes():
    g = build_default_state_graph()
    for node in ("autoregeneration_diagnostics", "degradation_state",
                 "repair_policy", "repair_action", "state_hygiene_manager",
                 "checkpoint_repair_manager", "reference_repair_manager",
                 "memory_hygiene_manager", "world_model_hygiene_manager",
                 "symbol_hygiene_manager", "habit_hygiene_manager",
                 "drift_recovery_manager", "repair_memory",
                 "autoregeneration_safety"):
        assert node in g.nodes


def test_state_graph_autoregeneration_edges():
    g = build_default_state_graph()
    edges = {(s, d) for s, d, _ in g.edges}
    assert ("repair_memory", "inner_map") in edges
    assert ("telemetry", "autoregeneration_diagnostics") in edges
