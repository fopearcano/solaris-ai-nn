"""Tests for developmental pressure flowing into homeostasis/executive."""

from __future__ import annotations

from solaris_ai_nn.executive.coordinator import ExecutiveLayer
from solaris_ai_nn.homeostasis.regulation import HomeostaticRegulator


def test_stagnation_biases_safe_exploration_suggestion():
    regulator = HomeostaticRegulator()
    result = regulator.update({"developmental": {
        "stagnation_pressure": 0.9, "drift_pressure": 0.0}})
    assert regulator.state.value("stagnation_pressure") == 0.9
    proposals = {c.proposal for c in result.desire_candidates
                 if not c.blocked}
    assert proposals & {"explore_safely", "look", "seek_signal"}
    # Through the executive: still a suggestion, still arbitrated.
    layer = ExecutiveLayer()
    decision = layer.decide(result.desire_candidates, context={}, step=1)
    assert decision.selected.committed is False


def test_high_drift_biases_stabilization_suggestion():
    regulator = HomeostaticRegulator()
    result = regulator.update({"developmental": {
        "stagnation_pressure": 0.0, "drift_pressure": 0.9}})
    assert regulator.state.value("drift_pressure") == 0.9
    proposals = {c.proposal for c in result.desire_candidates
                 if not c.blocked}
    assert "stabilize" in proposals or "reduce_activity" in proposals
    layer = ExecutiveLayer()
    decision = layer.decide(result.desire_candidates, context={}, step=1)
    assert decision.selected is not None


def test_memory_pressure_biases_consolidation():
    regulator = HomeostaticRegulator()
    result = regulator.update({"developmental": {
        "memory_pressure": 1.0}})
    assert regulator.state.value("consolidation_pressure") >= 1.0
    proposals = {c.proposal for c in result.desire_candidates
                 if not c.blocked}
    assert "consolidate_memory" in proposals


def test_degraded_identity_biases_review():
    regulator = HomeostaticRegulator()
    result = regulator.update({"developmental": {
        "identity_continuity": 0.3}})
    assert regulator.state.value(
        "identity_uncertainty_pressure") >= 0.7
    from solaris_ai_nn.homeostasis.needs import NeedType

    need = result.need_state.by_type(NeedType.REQUEST_OPERATOR_REVIEW)
    assert need is not None


def test_pressure_never_forces_unsafe_changes():
    regulator = HomeostaticRegulator()
    result = regulator.update({"developmental": {
        "stagnation_pressure": 1.0, "drift_pressure": 1.0,
        "memory_pressure": 1.0, "long_run_fatigue_proxy": 1.0}})
    # However extreme the pressure, the output stays candidates.
    for candidate in result.desire_candidates:
        assert candidate.to_canonical().proposal
    # And nothing real-world shaped survives the safety list.
    assert not any("motor" in c.proposal
                   for c in result.desire_candidates)
