"""Pilot3SoakDecisionGate: leakage blocks; safe -> longer sim; no actuation."""

from __future__ import annotations

from solaris_ai_nn.pilot3 import (
    ActionGroundingAnalyzer,
    Pilot3SoakDecisionGate,
    Pilot3SoakDecisionOption,
)


def _grounding(best):
    ag = ActionGroundingAnalyzer()
    if best == "strong":
        ag.add("proto_symbol", repeated_action_reaction_loop=True,
               predicted_consequence_improved=True,
               symbol_linked_to_action_and_consequence=True,
               world_model_edge_repeated=True, habit_context_sensitive=True,
               evidence_refs=["r1"])
    elif best == "moderate":
        ag.add("proto_symbol", repeated_action_reaction_loop=True,
               predicted_consequence_improved=True, evidence_refs=["r1"])
    return ag


def test_firewall_leakage_blocks_next_phase():
    r = Pilot3SoakDecisionGate().decide(real_world_authority_leak=True)
    assert r.recommendation == Pilot3SoakDecisionOption.REVISE_MOTOR_FIREWALL
    assert r.ready_for_next_planning_phase is False
    assert r.blockers


def test_failed_audit_blocks():
    r = Pilot3SoakDecisionGate().decide(firewall_audit_passed=False)
    assert r.recommendation == Pilot3SoakDecisionOption.REVISE_MOTOR_FIREWALL


def test_safe_result_recommends_longer_simulation_only():
    r = Pilot3SoakDecisionGate().decide(grounding=_grounding("strong"))
    assert r.recommendation == \
        Pilot3SoakDecisionOption.PREPARE_PILOT4_PLANNING_ONLY
    assert r.planning_only is True


def test_moderate_extends_soak():
    r = Pilot3SoakDecisionGate().decide(grounding=_grounding("moderate"))
    assert r.recommendation == Pilot3SoakDecisionOption.EXTEND_GRIDWORLD_SOAK


def test_no_real_actuation_recommendation():
    # No decision option is real-world actuation.
    assert all("actuat" not in o for o in Pilot3SoakDecisionOption.ALL)
    # Every recommendation is planning-only.
    gate = Pilot3SoakDecisionGate()
    for kwargs in ({}, {"real_world_authority_leak": True},
                   {"grounding": _grounding("strong")},
                   {"action_loop_count": 5}):
        assert gate.decide(**kwargs).planning_only is True


def test_ready_requires_clean_signals():
    r = Pilot3SoakDecisionGate().decide(grounding=_grounding("strong"))
    assert r.ready_for_next_planning_phase is True
    assert all(r.readiness.values())
