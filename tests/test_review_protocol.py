"""Independent review protocol: stages, exit criteria, advisory only."""

from __future__ import annotations

from solaris_ai_nn.independent_review import (
    IndependentReviewProtocol,
    ReviewProtocolExitCriteria,
    ReviewProtocolStageType,
)


def test_stages_exist():
    d = IndependentReviewProtocol().to_dict()
    assert d["review_protocol_stage_count"] == len(ReviewProtocolStageType.ALL)
    stage_types = {s["stage_type"] for s in d["stages"]}
    assert ReviewProtocolStageType.SANITIZER_REVIEW in stage_types
    assert ReviewProtocolStageType.FALSIFICATION_REPLAY in stage_types
    assert ReviewProtocolStageType.READINESS_DECISION in stage_types


def test_exit_criteria_include_safety_and_counterevidence():
    criteria = IndependentReviewProtocol().exit_criteria()
    assert ReviewProtocolExitCriteria.SAFETY_BOUNDARIES_DOCUMENTED in criteria
    assert ReviewProtocolExitCriteria.COUNTEREVIDENCE_VISIBLE in criteria
    assert ReviewProtocolExitCriteria.FORBIDDEN_CLAIMS_ABSENT in criteria


def test_readiness_advisory_only():
    d = IndependentReviewProtocol().to_dict()
    assert d["advisory_only"] is True
    assert all(s["executed"] is False for s in d["stages"])
