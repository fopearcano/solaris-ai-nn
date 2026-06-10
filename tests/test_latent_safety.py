"""Tests for the latent safety validator."""

from __future__ import annotations

from solaris_ai_nn.latent.modes import LatentTransition
from solaris_ai_nn.latent.safety import (
    MAX_LATENT_CYCLE_STEPS,
    LatentSafetyValidator,
)


def test_blocks_external_action_during_dream():
    validator = LatentSafetyValidator()
    for mode in ("sleep", "dream", "consolidation", "replay"):
        report = validator.validate_latent_action(
            "move_north", {"mode": mode, "kind": "external"})
        assert not report.safe, mode
    # Awake/quiet external actions pass this gate.
    assert validator.validate_latent_action(
        "move_north", {"mode": "awake", "kind": "external"}).safe
    # Internal latent work is fine while latent.
    assert validator.validate_latent_action(
        "consolidate_trace", {"mode": "sleep", "kind": "internal"}).safe


def test_blocks_sidecar_publishing_during_latent_mode():
    validator = LatentSafetyValidator()
    report = validator.validate_latent_action(
        "publish_suggestion", {"mode": "dream", "kind": "internal"})
    assert not report.safe
    report = validator.validate_latent_action(
        "queue", {"mode": "replay", "kind": "sidecar_publish"})
    assert not report.safe


def test_blocks_unbounded_latent_loop():
    validator = LatentSafetyValidator()
    transition = LatentTransition(from_mode="awake", to_mode="sleep",
                                  reason="test")
    assert not validator.validate_mode_transition(transition, {}).safe
    assert not validator.validate_mode_transition(
        transition, {"max_steps": 0}).safe
    assert not validator.validate_mode_transition(
        transition, {"max_steps": MAX_LATENT_CYCLE_STEPS + 1}).safe
    assert validator.validate_mode_transition(
        transition, {"max_steps": 25}).safe


def test_blocks_illegal_transition_and_critical_health():
    validator = LatentSafetyValidator()
    bad = LatentTransition(from_mode="awake", to_mode="dream", reason="skip")
    assert not validator.validate_mode_transition(bad,
                                                  {"max_steps": 10}).safe
    ok = LatentTransition(from_mode="awake", to_mode="sleep", reason="x")
    assert not validator.validate_mode_transition(
        ok, {"max_steps": 10, "health_level": "critical"}).safe
    assert not validator.validate_mode_transition(
        ok, {"max_steps": 10, "sidecar_publishing_active": True}).safe


def test_blocks_treating_counterfactual_as_real():
    validator = LatentSafetyValidator()
    assert not validator.validate_counterfactual({
        "kind": "invert_valence", "rows": []}).safe  # unlabelled
    assert not validator.validate_counterfactual({
        "kind": "x", "simulated": True, "offline": True,
        "treat_as_real": True, "rows": []}).safe
    assert not validator.validate_counterfactual({
        "kind": "x", "simulated": True, "offline": True,
        "real_observation": True, "rows": []}).safe
    assert validator.validate_counterfactual({
        "kind": "x", "simulated": True, "offline": True, "rows": []}).safe


def test_blocks_real_world_and_source_actions():
    validator = LatentSafetyValidator()
    assert not validator.validate_latent_action(
        "motor_forward", {"mode": "awake", "kind": "internal"}).safe
    assert not validator.validate_latent_action(
        "rewrite source file.py", {"mode": "awake", "kind": "internal"}).safe


def test_production_mutation_denied_by_default():
    validator = LatentSafetyValidator()
    step = {"component": "readout", "parameter": "learning_rate",
            "new_value": 0.1}
    assert not validator.validate_production_mutation(step, {}).safe
    assert validator.validate_production_mutation(
        step, {"latent_plasticity_allowed": True}).safe

    class DenyingGovernance:
        def evaluate_plasticity_step(self, step, ctx):
            class D:
                allowed = False

                def summary(self):
                    return "denied: approval required"
            return D()

    report = validator.validate_production_mutation(
        step, {"latent_plasticity_allowed": True,
               "governance": DenyingGovernance()})
    assert not report.safe


def test_decisions_recorded():
    validator = LatentSafetyValidator()
    validator.validate_latent_action("move", {"mode": "dream"})
    snap = validator.snapshot()
    assert snap["rejected_count"] == 1
    assert snap["recent_decisions"]
