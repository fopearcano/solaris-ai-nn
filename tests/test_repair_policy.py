"""Tests for the repair policy."""

from __future__ import annotations

import pytest

from solaris_ai_nn.autoregeneration.degradation import (
    DegradationSeverity,
    DegradationSignal,
    DegradationState,
    DegradationType,
)
from solaris_ai_nn.autoregeneration.repair_policy import (
    RepairPolicy,
    RepairPolicyMode,
)


def _state(*types):
    state = DegradationState()
    for t in types:
        state.add(DegradationSignal(type=t,
                                    severity=DegradationSeverity.WARNING,
                                    evidence_refs=["e"]))
    return state


def test_default_observe_only():
    assert RepairPolicy().mode == RepairPolicyMode.OBSERVE_ONLY


def test_observe_only_proposes_nothing():
    policy = RepairPolicy(mode=RepairPolicyMode.OBSERVE_ONLY)
    decisions = policy.propose(_state(DegradationType.MEMORY_BLOAT), {})
    assert decisions == []


def test_suggest_only_proposes_but_does_not_apply():
    policy = RepairPolicy(mode=RepairPolicyMode.SUGGEST_ONLY)
    decisions = policy.propose(_state(DegradationType.MEMORY_BLOAT), {})
    assert decisions
    assert all(not d.apply_allowed for d in decisions)


def test_safe_auto_repair_applies_low_risk():
    policy = RepairPolicy(mode=RepairPolicyMode.SAFE_AUTO_REPAIR)
    decisions = policy.propose(_state(DegradationType.MEMORY_BLOAT), {})
    assert any(d.apply_allowed for d in decisions)


def test_emergency_stabilization_restricted():
    policy = RepairPolicy(mode=RepairPolicyMode.SAFE_AUTO_REPAIR)
    # An emergency forces emergency-stabilization mode regardless of config.
    decisions = policy.propose(
        _state(DegradationType.MEMORY_BLOAT, DegradationType.DRIFT_RUNAWAY),
        {"emergency": True})
    assert decisions
    assert all(d.mode == RepairPolicyMode.EMERGENCY_STABILIZATION
               for d in decisions)
    # Only risk-reducing repairs may apply; memory compaction is not applied.
    applied = [d for d in decisions if d.apply_allowed]
    assert all(d.action.action_type in (
        "switch_to_stabilization_mode", "reduce_sampling_rate",
        "request_consolidation", "generate_operator_review_request",
        "no_repair") for d in applied)


def test_governed_repair_needs_approval_for_gov_action():
    policy = RepairPolicy(mode=RepairPolicyMode.GOVERNED_REPAIR)
    decisions = policy.propose(
        _state(DegradationType.CHECKPOINT_INCONSISTENCY), {})
    # Identity-affecting repair requires governance and is not applied
    # without approval.
    assert all(not d.apply_allowed for d in decisions
               if d.action.requires_governance)


def test_unknown_mode_rejected():
    with pytest.raises(ValueError):
        RepairPolicy(mode="recursive_self_improvement")
