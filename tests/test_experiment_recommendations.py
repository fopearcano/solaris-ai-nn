"""Experiment recommendations: ablation/control/falsification; no exec; safety."""

from __future__ import annotations

from solaris_ai_nn.review_assimilation import (
    RecommendationType,
    ReviewDrivenExperimentRecommender,
    ReviewerObjectionClassifier,
)


def _classify(objections):
    return ReviewerObjectionClassifier().classify(objections)


def test_control_falsification_recommendations_generated():
    objs = _classify([
        {"objection_id": "o1", "text": "Could be a passive parser artifact."},
        {"objection_id": "o2", "text": "No control arm."},
        {"objection_id": "o3", "text": "Insufficient replication."}])
    recs = ReviewDrivenExperimentRecommender().recommend(objections=objs, gaps=[])
    types = {r.recommendation_type for r in recs}
    assert RecommendationType.RUN_PASSIVE_PARSER_CONTROL in types
    assert RecommendationType.ADD_CONTROL_ARM in types
    assert RecommendationType.RUN_REPLICATION in types


def test_no_experiment_execution():
    objs = _classify([{"objection_id": "o1", "text": "fixture overfit"}])
    recs = ReviewDrivenExperimentRecommender().recommend(objections=objs, gaps=[])
    for r in recs:
        d = r.to_dict()
        assert d["executed"] is False
        assert d["creates_branch"] is False


def test_high_risk_requires_safety_context():
    objs = _classify([
        {"objection_id": "o1", "text": "Probably fixture overfit."}])
    recs = ReviewDrivenExperimentRecommender().recommend(objections=objs, gaps=[])
    # fixture overfit -> live-read-only comparison (high risk).
    live = [r for r in recs
            if r.recommendation_type ==
            RecommendationType.RUN_LIVE_READ_ONLY_COMPARISON]
    assert live and live[0].safety_context


def test_recommendations_are_experiment_inputs():
    objs = _classify([{"objection_id": "o1", "text": "no control arm"}])
    recs = ReviewDrivenExperimentRecommender().recommend(objections=objs, gaps=[])
    summary = ReviewDrivenExperimentRecommender.summary(recs)
    assert summary["experiment_input_count"] >= 1
