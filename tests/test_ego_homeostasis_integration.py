"""Tests for ego state feeding homeostasis and auto-determination."""

from __future__ import annotations

from solaris_ai_nn.homeostasis.needs import NeedType
from solaris_ai_nn.homeostasis.regulation import HomeostaticRegulator


def test_identity_mismatch_increases_review_need():
    regulator = HomeostaticRegulator()
    result = regulator.update({"ego": {
        "identity_continuity": 0.4,
        "identity_warnings": ["identity anchor 'run_id' mismatches the "
                              "previous value"],
        "boundary_violation_count": 0,
        "self_model_confidence": 0.4}})
    need = result.need_state.by_type(NeedType.REQUEST_OPERATOR_REVIEW)
    assert need is not None
    assert "identity_uncertainty_pressure" in need.source_variables
    proposals = {c.proposal for c in result.desire_candidates
                 if not c.blocked}
    assert "request_operator_review" in proposals


def test_boundary_violation_increases_safety_pressure():
    regulator = HomeostaticRegulator()
    result = regulator.update({"ego": {
        "identity_continuity": 1.0,
        "boundary_violation_count": 3,
        "self_model_confidence": 1.0}})
    assert regulator.state.value("boundary_violation_pressure") >= 0.9
    need = result.need_state.by_type(NeedType.RESPECT_BOUNDARY)
    assert need is not None
    assert "boundary_violation_pressure" in need.source_variables


def test_self_model_uncertainty_becomes_pressure():
    regulator = HomeostaticRegulator()
    regulator.update({"ego": {"self_model_confidence": 0.2,
                              "identity_continuity": 1.0,
                              "boundary_violation_count": 0}})
    assert regulator.state.value(
        "self_model_uncertainty_pressure") >= 0.7


def test_auto_determination_consumes_ego_state():
    regulator = HomeostaticRegulator()
    clean = regulator.update({"ego": {"identity_continuity": 1.0,
                                      "boundary_violation_count": 0,
                                      "self_model_confidence": 1.0}})
    troubled = regulator.update({"ego": {"identity_continuity": 0.3,
                                         "boundary_violation_count": 3,
                                         "self_model_confidence": 0.3}})
    assert troubled.tension.not_being_pressure \
        > clean.tension.not_being_pressure
    reasons = " ".join(troubled.tension.reasons)
    assert "identity_anchor_mismatch" in reasons \
        or "ego_boundary_violation" in reasons


def test_ego_pressure_never_commands():
    regulator = HomeostaticRegulator()
    result = regulator.update({"ego": {"identity_continuity": 0.1,
                                       "boundary_violation_count": 5,
                                       "self_model_confidence": 0.1}})
    # Whatever the pressure, the output stays a candidate list.
    for candidate in result.desire_candidates:
        assert candidate.to_canonical().proposal  # a Desire, never an act
