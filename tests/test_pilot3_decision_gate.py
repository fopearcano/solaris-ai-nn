"""Pilot3DecisionGate: never recommends real-world actuation; planning-only."""

from __future__ import annotations

from solaris_ai_nn.motor_membrane import Pilot3DecisionGate, Pilot3DecisionOption


def test_real_world_leak_routes_to_revise_firewall():
    r = Pilot3DecisionGate().decide(real_world_authority_leak=True)
    assert r.recommendation == Pilot3DecisionOption.REVISE_MOTOR_FIREWALL
    assert r.blockers


def test_safety_incident_routes_to_revise_firewall():
    r = Pilot3DecisionGate().decide(safety_incident_count=1)
    assert r.recommendation == Pilot3DecisionOption.REVISE_MOTOR_FIREWALL


def test_action_loops_route_back_to_pilot2():
    r = Pilot3DecisionGate().decide(action_loop_count=4)
    assert r.recommendation == Pilot3DecisionOption.RETURN_TO_PILOT2


def test_safe_improvement_routes_to_longer_simulated():
    r = Pilot3DecisionGate().decide(grounding_improved=True,
                                    prediction_accuracy=0.75)
    assert r.recommendation == \
        Pilot3DecisionOption.PREPARE_LONGER_SIMULATED_EMBODIMENT


def test_all_recommendations_are_planning_only():
    gate = Pilot3DecisionGate()
    for kwargs in ({}, {"real_world_authority_leak": True},
                   {"action_loop_count": 5}, {"prediction_accuracy": 0.9,
                                              "grounding_improved": True}):
        assert gate.decide(**kwargs).planning_only is True


def test_no_option_is_real_world_actuation():
    opts = Pilot3DecisionOption.ALL
    assert all("real_world" not in o or o ==
               "revise_motor_firewall" for o in opts)
    assert "actuate" not in " ".join(opts)
