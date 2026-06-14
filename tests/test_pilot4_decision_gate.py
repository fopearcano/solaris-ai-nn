"""Pilot4DecisionGate: leak->revise firewall; incomplete->sim-only; no enable."""

from __future__ import annotations

from solaris_ai_nn.pilot4_planning import Pilot4DecisionGate, Pilot4DecisionOption


def test_critical_firewall_finding_recommends_revise_firewall():
    r = Pilot4DecisionGate().decide(pilot3_firewall_critical_findings=1)
    assert r.recommendation == Pilot4DecisionOption.REVISE_FIREWALL


def test_incomplete_consent_recommends_remain_simulation_only():
    r = Pilot4DecisionGate().decide(consent_complete=False,
                                    threat_model_complete=True,
                                    audit_requirements_complete=True)
    assert r.recommendation == Pilot4DecisionOption.REMAIN_SIMULATION_ONLY


def test_missing_pilot3_recommends_repeat_pilot3():
    r = Pilot4DecisionGate().decide(pilot3_data_present=False)
    assert r.recommendation == Pilot4DecisionOption.REPEAT_PILOT3


def test_complete_recommends_draft_future_protocol_only():
    r = Pilot4DecisionGate().decide(consent_complete=True,
                                    threat_model_complete=True,
                                    audit_requirements_complete=True)
    assert r.recommendation == \
        Pilot4DecisionOption.DRAFT_FUTURE_SINGLE_ACTION_PROTOCOL


def test_no_option_enables_real_actuation():
    assert all("enable" not in o for o in Pilot4DecisionOption.ALL)
    gate = Pilot4DecisionGate()
    for kwargs in ({}, {"pilot3_firewall_critical_findings": 1},
                   {"consent_complete": True, "threat_model_complete": True,
                    "audit_requirements_complete": True}):
        r = gate.decide(**kwargs)
        assert r.planning_only is True
        assert r.real_world_actuation_enabled is False
