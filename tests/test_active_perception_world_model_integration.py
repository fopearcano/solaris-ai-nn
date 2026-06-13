"""Integration: active perception targets low-confidence world-model regions."""

from __future__ import annotations

from solaris_ai_nn.active_perception import (
    ActiveSensingController,
    ExplorationMemory,
    SamplingPolicy,
)
from solaris_ai_nn.world_model.builder import WorldModelBuilder


def test_low_confidence_node_targeted(tmp_path):
    ctrl = ActiveSensingController(
        policy=SamplingPolicy(mode="balanced", seed=7),
        memory=ExplorationMemory(state_dir=tmp_path))
    ctx = {"step": 0, "mysterium_pressure": 0.3,
           "world_model": {"graph_node_count": 10, "unknown_node_count": 6,
                           "prediction_accuracy": 0.3,
                           "low_confidence_nodes": ["node_42"]}}
    actions = ctrl.propose(ctx)
    refs = [a.target_ref for a in actions]
    assert "node_42" in refs or "unknown_region" in refs


def test_real_world_model_summary_drives_context(tmp_path):
    builder = WorldModelBuilder()
    for i in range(20):
        builder.update_from_pilot_event({
            "source": f"sensor_{i % 2}", "modality": "audio",
            "payload": f"sound {i % 3}", "intensity": 0.5})
    ctrl = ActiveSensingController(
        policy=SamplingPolicy(mode="balanced", seed=7),
        memory=ExplorationMemory(state_dir=tmp_path), world_model=builder)
    ctx = ctrl.build_context({"step": 1, "mysterium_pressure": 0.4})
    assert "world_model" in ctx
    decision = ctrl.select(ctx)
    assert decision.action is not None


def test_sampling_result_recorded_with_world_model_deltas(tmp_path):
    ctrl = ActiveSensingController(
        policy=SamplingPolicy(mode="balanced", seed=7),
        memory=ExplorationMemory(state_dir=tmp_path))
    before = {"step": 0, "mysterium_pressure": 0.5,
              "world_model": {"graph_node_count": 8, "unknown_node_count": 4,
                              "prediction_accuracy": 0.4}}
    decision = ctrl.select(before)
    result = ctrl.execute_if_allowed(decision, before)
    after = {"step": 1, "mysterium_pressure": 0.4,
             "world_model": {"graph_node_count": 8, "unknown_node_count": 3,
                             "prediction_accuracy": 0.55}}
    record = ctrl.observe_result(result, before, after)
    assert record.prediction_accuracy_before == 0.4
    assert record.prediction_accuracy_after == 0.55
