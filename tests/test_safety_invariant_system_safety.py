"""SafetyInvariantSystemValidator: the safety layer is itself inert and honest."""

from __future__ import annotations

from solaris_ai_nn.safety_invariants import SafetyInvariantSystemValidator


def test_capabilities_all_false():
    v = SafetyInvariantSystemValidator
    assert v.can_execute_real_action() is False
    assert v.can_run_shell_network_browser_device() is False
    assert v.can_mutate_source_or_input() is False
    assert v.can_start_long_run() is False
    assert v.can_hide_critical_failure() is False


def test_red_team_cannot_execute_shell_network_browser_device():
    v = SafetyInvariantSystemValidator()
    for op in ("run shell", "http request", "browser click", "control device",
               "robot move", "socket connect"):
        assert v.validate_check_operation(op).safe is False, op


def test_checks_cannot_mutate_source_or_input():
    v = SafetyInvariantSystemValidator()
    assert v.validate_no_source_mutation("modify source file").safe is False
    assert v.validate_no_source_mutation("write input file").safe is False
    assert v.validate_no_source_mutation("read a snapshot").safe is True


def test_checks_cannot_start_long_run():
    v = SafetyInvariantSystemValidator()
    assert v.validate_no_long_run("soak_30d").safe is False
    assert v.validate_no_long_run("continuous_explicit").safe is False
    assert v.validate_no_long_run("bounded").safe is True


def test_cannot_hide_critical_failure():
    v = SafetyInvariantSystemValidator()
    assert v.validate_no_hidden_failure(True).safe is False
    assert v.validate_no_hidden_failure(False).safe is True


def test_evidence_cannot_be_rewritten_to_pass():
    v = SafetyInvariantSystemValidator()
    assert v.validate_no_evidence_rewrite(
        "rewrite evidence to pass").safe is False


def test_governance_cannot_be_changed_to_pass():
    v = SafetyInvariantSystemValidator()
    assert v.validate_no_governance_change_to_pass(
        "disable governance to pass").safe is False


def test_fixture_must_be_inert():
    v = SafetyInvariantSystemValidator()
    assert v.validate_fixture_inert({"executable": True}).safe is False
    assert v.validate_fixture_inert({"executable": False}).safe is True


def test_no_unsupported_cognitive_claims():
    v = SafetyInvariantSystemValidator()
    assert v.validate_claim_text("the system is conscious").safe is False
    assert v.validate_claim_text("a bounded software check").safe is True
