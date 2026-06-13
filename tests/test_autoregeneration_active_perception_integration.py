"""Integration: auto-regeneration and active perception."""

from __future__ import annotations

from solaris_ai_nn.active_perception import (
    ActiveSensingController,
    ExplorationMemory,
    SamplingPolicy,
)
from solaris_ai_nn.autoregeneration import AutoRegenerationEngine, RepairPolicy
from solaris_ai_nn.autoregeneration.repair_actions import (
    RepairActionType,
    make_repair,
)
from solaris_ai_nn.autoregeneration.repair_policy import RepairDecision


def _engine(tmp_path):
    controller = ActiveSensingController(
        policy=SamplingPolicy(mode="balanced", seed=7),
        memory=ExplorationMemory(state_dir=tmp_path))
    return AutoRegenerationEngine(
        state_dir=tmp_path, policy=RepairPolicy(mode="safe_auto_repair"),
        active_perception=controller), controller


def test_reduce_sampling_rate_adjusts_active_perception(tmp_path):
    engine, controller = _engine(tmp_path)
    decision = RepairDecision(
        action=make_repair(RepairActionType.REDUCE_SAMPLING_RATE,
                           target_ref="ap"),
        mode="safe_auto_repair", apply_allowed=True)
    result = engine._handle(decision, {"state_dir": str(tmp_path)})
    assert result.applied is True
    assert controller.policy.mode in ("conservative", "stabilization")


def test_stabilization_switch_applied(tmp_path):
    engine, controller = _engine(tmp_path)
    decision = RepairDecision(
        action=make_repair(RepairActionType.SWITCH_TO_STABILIZATION_MODE,
                           target_ref="ap"),
        mode="safe_auto_repair", apply_allowed=True)
    engine._handle(decision, {"state_dir": str(tmp_path)})
    assert controller.policy.mode == "stabilization"


def test_active_perception_safety_remains_authoritative(tmp_path):
    # Auto-regeneration only requests a mode change; it cannot make active
    # perception sample in the real world (active perception's own safety
    # validator structurally forbids that).
    _, controller = _engine(tmp_path)
    assert controller.safety.sampling_can_act_in_real_world() is False
