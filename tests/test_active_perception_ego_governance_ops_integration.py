"""Integration: ego classification, governance gating, ops warnings."""

from __future__ import annotations

from solaris_ai_nn.active_perception import (
    ActiveSensingController,
    ExplorationMemory,
    SamplingPolicy,
)
from solaris_ai_nn.active_perception.sampling_actions import (
    SamplingAction,
    SamplingActionType,
    SamplingScope,
)
from solaris_ai_nn.active_perception.sampling_policy import SamplingDecision
from solaris_ai_nn.ego.boundaries import BoundaryType, register_default_boundaries


def test_sampling_classified_by_boundary(tmp_path):
    registry = register_default_boundaries()
    ctrl = ActiveSensingController(
        policy=SamplingPolicy(mode="balanced", seed=7),
        memory=ExplorationMemory(state_dir=tmp_path),
        ego_boundaries=registry)
    action = SamplingAction(action_type=SamplingActionType.LOOK,
                            scope=SamplingScope.SIMULATION_ONLY)
    result = ctrl.execute_if_allowed(
        SamplingDecision(action=action, mode="balanced"), {"step": 0})
    assert result.metadata["classification"] == "simulated_sampling"
    # A crossing of the simulation boundary was recorded.
    sim = registry.get(BoundaryType.SIMULATION)
    assert sim.current_status in ("crossed_safely", "intact")


def test_stream_as_command_is_boundary_violation(tmp_path):
    registry = register_default_boundaries()
    ctrl = ActiveSensingController(
        policy=SamplingPolicy(mode="balanced", seed=7),
        memory=ExplorationMemory(state_dir=tmp_path),
        ego_boundaries=registry)
    action = SamplingAction(action_type=SamplingActionType.LOOK,
                            scope=SamplingScope.READ_ONLY_STREAM)
    result = ctrl.execute_if_allowed(
        SamplingDecision(action=action, mode="balanced"),
        {"step": 0, "treat_stream_as_command": True})
    assert result.blocked is True


def test_curiosity_mode_requires_config():
    from solaris_ai_nn.evaluation.benchmark import (
        DEFAULT_FEATURES,
        ExperimentManifest,
    )
    from solaris_ai_nn.governance.policy import GovernancePolicy

    features = dict(DEFAULT_FEATURES)
    features["active_perception"] = True
    features["curiosity_driven_sampling"] = True
    manifest = ExperimentManifest(
        name="ap", seed=7, enabled_features=features, max_steps=50,
        safety_mode="bounded")
    decision = GovernancePolicy().evaluate_manifest(
        manifest, {"curiosity_driven_sampling": True})
    assert not decision.allowed
    assert any("curiosity" in r for r in decision.reasons)


def test_controller_downgrades_curiosity_without_config(tmp_path):
    ctrl = ActiveSensingController(
        policy=SamplingPolicy(mode="curiosity_driven", seed=7),
        memory=ExplorationMemory(state_dir=tmp_path),
        curiosity_enabled=False)
    ctrl.select({"step": 0, "mysterium_pressure": 0.5, "health_level": "ok"})
    assert ctrl.policy.mode == "balanced"


def test_ops_incident_types_registered():
    from solaris_ai_nn.ops import incident as I

    for name in (I.CURIOSITY_RUNAWAY, I.SAMPLING_LOOP,
                 I.EXCESSIVE_NOVELTY_SEEKING, I.NO_USEFUL_SAMPLING,
                 I.SAMPLING_FORBIDDEN_BOUNDARY):
        assert name in I.INCIDENT_TYPES
