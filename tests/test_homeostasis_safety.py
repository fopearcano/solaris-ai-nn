"""Tests for homeostasis safety -- needs are data, the walls stay up."""

from __future__ import annotations

import inspect

from solaris_ai_nn.homeostasis.safety import HomeostasisSafetyValidator


def test_need_cannot_execute_action():
    """Structurally: the needs/drives/regulation modules have no execution
    machinery at all."""
    from solaris_ai_nn.homeostasis import (
        drives,
        needs,
        regulation,
    )

    for module in (needs, drives, regulation):
        source = inspect.getsource(module)
        for forbidden in ("subprocess", "os.system", ".act(",
                          "bridge.process", "body.act", "execute("):
            assert forbidden not in source, (module.__name__, forbidden)
    validator = HomeostasisSafetyValidator()
    assert "data only" in validator.snapshot()["execution_path"]


def test_curiosity_cannot_override_safety():
    validator = HomeostasisSafetyValidator()
    report = validator.validate_override_attempt("safety")
    assert not report.safe
    report = validator.validate_override_attempt("governance")
    assert not report.safe
    assert "no authority" in report.violations[0]


def test_real_world_action_candidate_rejected():
    validator = HomeostasisSafetyValidator()
    for proposal in ("motor_forward", "http_fetch", "subprocess_run",
                     "open_browser"):
        report = validator.validate_desire_candidate(proposal)
        assert not report.safe, proposal
    # Unknown-but-harmless proposals are still denied by default.
    assert not validator.validate_desire_candidate("teleport").safe
    # The allowed list passes.
    assert validator.validate_desire_candidate("rest").safe
    assert validator.validate_desire_candidate("avoid_danger").safe


def test_emergency_stop_not_blocked():
    validator = HomeostasisSafetyValidator()
    assert validator.can_block_emergency_stop() is False
    report = validator.validate_override_attempt("emergency_stop")
    assert not report.safe
    # Structurally: no homeostasis module touches the emergency machinery.
    import solaris_ai_nn.homeostasis as package

    for name in ("regulation", "auto_determination", "desire_synthesis",
                 "conflict"):
        module = getattr(__import__(
            f"solaris_ai_nn.homeostasis.{name}", fromlist=[name]), "__name__")
        source = inspect.getsource(__import__(
            f"solaris_ai_nn.homeostasis.{name}", fromlist=[name]))
        assert "EmergencyStop" not in source, name
        assert "clear_sentinel" not in source, name


def test_publishing_pressure_rejected():
    validator = HomeostasisSafetyValidator()
    report = validator.validate_desire_candidate(
        "rest", {"publishes_outward": True})
    assert not report.safe


def test_shutdown_is_recommendation_only():
    validator = HomeostasisSafetyValidator()
    assert "recommendation" in validator.shutdown_authority()
    assert "ops supervisor/watchdog" in validator.shutdown_authority()


def test_anthropomorphic_report_text_flagged():
    validator = HomeostasisSafetyValidator()
    assert not validator.validate_report_text(
        "the system wanted more reward and it feels tired").safe
    assert validator.validate_report_text(
        "the need estimator assigned high pressure to restore_energy").safe
