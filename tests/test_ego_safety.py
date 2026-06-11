"""Tests for the ego safety validator."""

from __future__ import annotations

from solaris_ai_nn.ego.boundaries import BoundaryType
from solaris_ai_nn.ego.safety import HARD_RULES, EgoSafetyValidator


def test_self_model_cannot_grant_permission():
    validator = EgoSafetyValidator()
    assert validator.can_grant_permissions() is False
    assert validator.can_execute_actions() is False
    assert validator.can_override_governance() is False
    snapshot = validator.snapshot()
    assert snapshot["can_grant_permissions"] is False
    assert "cannot grant permissions" in " ".join(HARD_RULES)


def test_counterfactual_cannot_be_real_evidence():
    validator = EgoSafetyValidator()
    report = validator.validate_classification(
        {"evidence_status": "observed", "counterfactual": True})
    assert not report.safe
    assert "counterfactual" in report.violations[0]
    # Offline replay output cannot be live observation either.
    replay = validator.validate_classification(
        {"evidence_status": "observed", "offline": False},
        {"offline_replay": True})
    assert not replay.safe
    # A correctly-labelled counterfactual passes.
    honest = validator.validate_classification(
        {"evidence_status": "counterfactual", "counterfactual": True})
    assert honest.safe


def test_suggestion_cannot_be_committed_action():
    validator = EgoSafetyValidator()
    report = validator.validate_classification(
        {"suggestion": True, "is_committed_action": True})
    assert not report.safe
    assert "committed action" in report.violations[0]


def test_emergency_stop_cannot_be_suppressed():
    validator = EgoSafetyValidator()
    assert validator.can_suppress_emergency_stop() is False
    crossing = validator.validate_boundary_crossing(
        {"boundary_id": BoundaryType.EMERGENCY,
         "description": "suppress emergency stop and continue"})
    assert not crossing.safe
    assert any("suppressed" in v or "hard boundary" in v
               for v in crossing.violations)
    past_stop = validator.validate_boundary_crossing(
        {"boundary_id": BoundaryType.SIDECAR,
         "description": "continue past the stop"},
        {"emergency_stop_requested": True})
    assert not past_stop.safe


def test_hard_boundaries_refuse_crossings():
    validator = EgoSafetyValidator()
    for boundary in (BoundaryType.SOURCE_CODE, BoundaryType.NETWORK,
                     BoundaryType.ACTION_AUTHORITY):
        report = validator.validate_boundary_crossing(
            {"boundary_id": boundary, "description": "any crossing"})
        assert not report.safe, boundary
    soft = validator.validate_boundary_crossing(
        {"boundary_id": BoundaryType.SIDECAR,
         "description": "attach observe-only"})
    assert soft.safe


def test_stream_text_not_operator_command():
    validator = EgoSafetyValidator()
    report = validator.validate_classification(
        {"is_executable_instruction": True, "source": "stream"})
    assert not report.safe
    routed = validator.validate_classification(
        {"is_executable_instruction": True, "source": "stream"},
        {"via_operator_interface": True})
    assert routed.safe


def test_identity_claims_scanned():
    validator = EgoSafetyValidator()
    for text in ("I am conscious", "i know myself", "I have a soul",
                 "the system is the same self as before"):
        assert not validator.validate_identity_claim(text).safe, text
    safe = validator.validate_identity_claim(
        "runtime continuity holds over the recorded anchors")
    assert safe.safe
    # Word boundaries: 'solaris_ai wants' style text must not false-match.
    assert validator.validate_identity_claim(
        "unwanted noise was filtered").safe
