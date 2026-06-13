"""Tests for the hypothesis schema."""

from __future__ import annotations

import pytest

from solaris_ai_nn.hypothesis.hypotheses import (
    Hypothesis,
    HypothesisConfidence,
    HypothesisScope,
    HypothesisStatus,
    HypothesisType,
)


def test_thirteen_hypothesis_types():
    assert len(HypothesisType.ALL) == 13


def test_nine_statuses():
    assert len(HypothesisStatus.ALL) == 9
    for s in ("proposed", "scheduled", "testing", "supported", "weakened",
              "falsified", "inconclusive", "unsafe_to_test", "expired"):
        assert s in HypothesisStatus.ALL


def test_six_scopes():
    assert len(HypothesisScope.ALL) == 6


def test_hypothesis_serializes():
    h = Hypothesis(type=HypothesisType.PREDICTION,
                   statement="pattern A may predict B",
                   required_scope=HypothesisScope.NURSERY_ONLY)
    data = h.to_dict()
    assert data["type"] == "prediction_hypothesis"
    assert data["required_scope"] == "nursery_only"
    assert data["status"] == "proposed"
    assert "confidence_band" in data
    assert Hypothesis.from_dict(data).statement == h.statement


def test_statement_not_anthropomorphic_required():
    # The schema does not require any belief/want wording; a plain grounded
    # statement is valid.
    h = Hypothesis(type=HypothesisType.WORLD_MODEL_EDGE,
                   statement="edge x|predicts|y may be weak")
    assert "believe" not in h.statement
    assert "want" not in h.statement


def test_unknown_type_rejected():
    with pytest.raises(ValueError):
        Hypothesis(type="metaphysics_hypothesis", statement="x")


def test_unknown_scope_rejected():
    with pytest.raises(ValueError):
        Hypothesis(type=HypothesisType.PREDICTION, statement="x",
                   required_scope="real_world")


def test_confidence_bounded_update():
    # Confidence never jumps more than MAX_STEP.
    assert HypothesisConfidence.bounded_update(0.5, 0.9) == 0.5 + \
        HypothesisConfidence.MAX_STEP
    assert HypothesisConfidence.bounded_update(0.5, -0.9) == 0.5 - \
        HypothesisConfidence.MAX_STEP
    assert HypothesisConfidence.band(0.8) == "high"


def test_dedup_key_stable():
    h1 = Hypothesis(type=HypothesisType.PREDICTION, statement="s",
                    target_ref="t")
    h2 = Hypothesis(type=HypothesisType.PREDICTION, statement="s2",
                    target_ref="t")
    assert h1.dedup_key == h2.dedup_key
