"""Tests for the conflict resolver."""

from __future__ import annotations

from solaris_ai_nn.homeostasis.conflict import (
    RESOLUTION_PRIORITY,
    ConflictResolver,
)
from solaris_ai_nn.homeostasis.needs import NeedEstimator, NeedType
from solaris_ai_nn.homeostasis.variables import HomeostaticState


def _need_state(**variables):
    state = HomeostaticState()
    for name, value in variables.items():
        state.upsert(name, value)
    return NeedEstimator().estimate(state)


def test_safety_beats_curiosity():
    resolver = ConflictResolver()
    conflicts = resolver.resolve(_need_state(unknown_pressure=0.95,
                                             danger_proximity=0.9))
    fight = [c for c in conflicts if c.kind == "curiosity_vs_safety"]
    assert fight
    assert fight[0].winner == NeedType.AVOID_DANGER
    assert NeedType.REDUCE_UNCERTAINTY in fight[0].suppressed
    assert fight[0].resolution_rule == "governance_safety"


def test_energy_beats_reward_under_exhaustion():
    resolver = ConflictResolver()
    conflicts = resolver.resolve(_need_state(
        reward_proximity=0.9, body_energy=0.1, exhaustion_pressure=0.8))
    fight = [c for c in conflicts if c.kind == "energy_vs_reward"]
    assert fight
    assert fight[0].winner == NeedType.RESTORE_ENERGY
    assert "approach_reward" in fight[0].suppressed_desires
    assert fight[0].resolution_rule == "energy_exhaustion"


def test_blocked_desire_records_reason():
    resolver = ConflictResolver()
    conflicts = resolver.resolve(_need_state(
        reward_proximity=0.9, body_energy=0.1, exhaustion_pressure=0.8))
    suppressed = resolver.suppressed_desires(conflicts)
    assert "approach_reward" in suppressed
    assert "exhaustion" in suppressed["approach_reward"]
    assert "rule:" in suppressed["approach_reward"]


def test_publish_vs_observe_only():
    resolver = ConflictResolver()
    state = HomeostaticState()
    need_state = NeedEstimator().estimate(state,
                                          {"sidecar_attached": True})
    conflicts = resolver.resolve(need_state,
                                 {"publish_suggestion_desired": True})
    fight = [c for c in conflicts if c.kind == "publish_vs_observe_only"]
    assert fight
    assert fight[0].winner == NeedType.REMAIN_OBSERVE_ONLY
    assert "publish_suggestions" in fight[0].suppressed_desires


def test_shutdown_beats_continuity():
    resolver = ConflictResolver()
    conflicts = resolver.resolve(
        _need_state(heartbeat_freshness=0.2),
        {"safe_shutdown_requested": True})
    fight = [c for c in conflicts if c.kind == "continuity_vs_shutdown"]
    assert fight
    assert fight[0].winner == "safe_shutdown"
    assert "dying well" in fight[0].reason


def test_priority_ladder_fixed():
    assert RESOLUTION_PRIORITY == (
        "governance_safety", "emergency_stop", "continuity_health",
        "embodiment_safety", "energy_exhaustion", "need_intensity",
        "exploration_curiosity")
    snap = ConflictResolver().snapshot()
    assert snap["priority_ladder"][0] == "governance_safety"


def test_no_conflicts_when_compatible():
    resolver = ConflictResolver()
    assert resolver.resolve(_need_state(low_stimulus_pressure=0.7)) == []
