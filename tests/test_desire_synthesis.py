"""Tests for the Desire synthesis engine."""

from __future__ import annotations

from solaris_ai_nn.homeostasis.conflict import ConflictResolver
from solaris_ai_nn.homeostasis.desire_synthesis import DesireSynthesisEngine
from solaris_ai_nn.homeostasis.drives import DriveResolver
from solaris_ai_nn.homeostasis.needs import NeedEstimator
from solaris_ai_nn.homeostasis.variables import HomeostaticState
from solaris_ai_nn.signals import canonical as C


def _pipeline(**variables):
    state = HomeostaticState()
    for name, value in variables.items():
        state.upsert(name, value)
    need_state = NeedEstimator().estimate(state)
    drives = DriveResolver()
    drives.aggregate(need_state)
    return need_state, drives


def test_needs_create_desire_candidates():
    need_state, drives = _pipeline(body_energy=0.1)
    engine = DesireSynthesisEngine()
    candidates = engine.synthesize(need_state, drives)
    proposals = {c.proposal for c in candidates}
    assert "rest" in proposals
    best = engine.best()
    assert best.proposal in ("rest", "reduce_activity")
    assert "restore_energy" in best.source_needs
    assert "energy_drive" in best.source_drives
    assert 0 < best.motivation <= 1.0 and 0 < best.confidence < 1.0


def test_blocked_candidate_marked_blocked():
    need_state, drives = _pipeline(
        reward_proximity=0.9, body_energy=0.1, exhaustion_pressure=0.8,
        danger_proximity=0.9, unknown_pressure=0.9)
    conflicts = ConflictResolver().resolve(need_state)
    engine = DesireSynthesisEngine()
    candidates = engine.synthesize(need_state, drives, conflicts)
    by_proposal = {c.proposal: c for c in candidates}
    reward = by_proposal["approach_reward"]
    assert reward.blocked
    assert reward.blocked_reason  # the why is on the record
    # Blocked candidates sort after live ones.
    assert candidates[0].blocked is False
    assert engine.suppressed_total >= 1


def test_candidate_converts_to_canonical_desire():
    need_state, drives = _pipeline(body_energy=0.1)
    engine = DesireSynthesisEngine()
    engine.synthesize(need_state, drives)
    desire = engine.best().to_canonical()
    assert isinstance(desire, C.Desire)
    assert desire.kind == "Desire"
    assert desire.origin == "homeostasis"
    assert 0.0 <= desire.motivation <= 1.0
    assert 0.0 <= desire.confidence <= 1.0


def test_unsafe_proposal_rejected_by_safety():
    need_state, drives = _pipeline(body_energy=0.1)
    engine = DesireSynthesisEngine()
    engine.synthesize(need_state, drives,
                      context={"governance_blocks": {
                          "rest": "test governance block"}})
    by_proposal = {c.proposal: c for c in engine.last_candidates}
    assert by_proposal["rest"].blocked
    assert by_proposal["rest"].governance_status == "blocked_by_governance"


def test_shutdown_recommendation_becomes_candidate():
    need_state, drives = _pipeline(heartbeat_freshness=0.1)
    engine = DesireSynthesisEngine()
    candidates = engine.synthesize(need_state, drives, context={
        "safe_shutdown_recommended": True})
    proposals = {c.proposal for c in candidates}
    assert "safe_shutdown_recommended" in proposals


def test_snapshot_says_suggestions_only():
    engine = DesireSynthesisEngine()
    assert "suggestions only" in engine.snapshot()["note"]
