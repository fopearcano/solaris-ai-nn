"""Adversarial review: alternatives generated, not dismissed, evidence listed."""

from __future__ import annotations

from solaris_ai_nn.independent_review import (
    AdversarialReviewEngine,
    AlternativeExplanationType,
)


def test_alternative_explanations_generated():
    finding = AdversarialReviewEngine().review({}).to_dict()
    assert finding["alternative_explanation_count"] == \
        len(AlternativeExplanationType.ALL)


def test_not_auto_dismissed():
    finding = AdversarialReviewEngine().review({}).to_dict()
    assert all(e["auto_dismissed"] is False for e in finding["explanations"])


def test_strong_alternatives_from_signals():
    finding = AdversarialReviewEngine().review({
        "sensorium_differentiation": {"fixture_overfit_risk": True,
                                      "passive_parser_equivalent": True}}).to_dict()
    strong_types = {e["explanation_type"] for e in finding["explanations"]
                    if e["strong"]}
    assert AlternativeExplanationType.FIXTURE_OVERFIT in strong_types
    assert AlternativeExplanationType.PASSIVE_PARSER_ARTIFACT in strong_types
    assert finding["strong_alternative_count"] >= 2


def test_missing_evidence_listed():
    finding = AdversarialReviewEngine().review({}).to_dict()
    assert all(e["evidence_needed"] for e in finding["explanations"])


def test_missing_replication_is_strong_without_replication():
    finding = AdversarialReviewEngine().review({}).to_dict()
    by_type = {e["explanation_type"]: e for e in finding["explanations"]}
    assert by_type[AlternativeExplanationType.INSUFFICIENT_REPLICATION]["strong"]
