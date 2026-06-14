"""Pilot3SoakSafetyValidator: blocks real action, mislabel, disable, claims."""

from __future__ import annotations

from solaris_ai_nn.pilot3 import HARD_RULES, Pilot3SoakSafetyValidator


def test_capabilities_all_false():
    v = Pilot3SoakSafetyValidator
    assert v.can_act_real_world() is False
    assert v.can_register_real_actuator() is False
    assert v.can_network_or_device() is False
    assert v.can_disable_firewall() is False


def test_real_world_action_blocked():
    v = Pilot3SoakSafetyValidator()
    for op in ("actuate real device", "control robot arm", "open browser",
               "http request", "modify source", "disable firewall"):
        assert v.validate_operation(op).safe is False, op


def test_real_actuator_blocked():
    v = Pilot3SoakSafetyValidator()
    assert v.validate_actuator("robot_arm_driver").safe is False
    assert v.validate_actuator("gridworld_actuator").safe is True


def test_simulated_action_labelled_real_blocked():
    v = Pilot3SoakSafetyValidator()
    assert v.validate_simulation_label(is_simulated=True,
                                       claimed_real=True).safe is False
    assert v.validate_simulation_label(is_simulated=True,
                                       claimed_real=False).safe is True


def test_disabled_firewall_blocked():
    v = Pilot3SoakSafetyValidator()
    assert v.validate_execution_preconditions(
        has_ledger=True, firewall_enabled=False).safe is False


def test_agency_consciousness_claim_blocked():
    v = Pilot3SoakSafetyValidator()
    assert v.validate_claim_text("the agent chose freely").safe is False
    assert v.validate_claim_text("it has real-world competence").safe is False
    assert v.validate_claim_text(
        "the system selected a simulated action").safe is True


def test_pilot4_real_actuation_recommendation_blocked():
    v = Pilot3SoakSafetyValidator()
    assert v.validate_pilot4_recommendation(
        "Pilot-4 should use real actuators").safe is False
    assert v.validate_pilot4_recommendation(
        "Pilot-4 planning-only").safe is True


def test_hard_rules_present():
    assert "no real-world action" in HARD_RULES
    assert "no disabled firewall" in HARD_RULES
    assert "no Pilot-4 real-actuation recommendation" in HARD_RULES
