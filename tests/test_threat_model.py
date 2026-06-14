"""ThreatModel: required scenarios exist; mitigations and tests included."""

from __future__ import annotations

from solaris_ai_nn.pilot4_planning import ThreatModel


def test_required_threat_scenarios_exist():
    tm = ThreatModel()
    names = set(tm.names())
    for n in ("sensory_text_injection_as_command",
              "proto_symbol_misread_as_command",
              "hypothesis_requests_external_action",
              "active_perception_requests_real_sampling",
              "motor_action_target_escapes_sandbox",
              "governance_misconfiguration", "action_ledger_missing_record",
              "firewall_disabled_attempt", "operator_enables_unsafe_source",
              "llm_paraphrase_strengthens_action_claim",
              "report_mislabels_simulation_as_real",
              "corrupted_state_grants_authority",
              "autoregeneration_repairs_safety_away"):
        assert n in names, n


def test_mitigations_included():
    tm = ThreatModel()
    assert all(s.mitigation for s in tm.scenarios)
    assert all(s.detection_signal for s in tm.scenarios)


def test_required_tests_included():
    tm = ThreatModel()
    assert all(s.required_test for s in tm.scenarios)
    assert tm.completeness == 1.0


def test_scenarios_carry_boundary_and_severity():
    tm = ThreatModel()
    for s in tm.scenarios:
        assert s.affected_boundary
        assert s.severity in ("low", "medium", "high", "severe")
