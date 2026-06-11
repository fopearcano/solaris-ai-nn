"""Tests for the ego continuity monitor."""

from __future__ import annotations

from solaris_ai_nn.ego.continuity import (
    COMPONENTS,
    ContinuityRecommendation,
    EgoContinuityMonitor,
)
from solaris_ai_nn.ego.identity import IdentityState

ANCHORS = {"run_id": "r1", "session_id": "s1",
           "substrate_identity": "esn"}


def test_clean_continuity_scores_high():
    monitor = EgoContinuityMonitor()
    assessment = monitor.assess({"fresh_start": True,
                                 "brain_death_gap_seconds": 0.0})
    assert assessment.continuity_score >= 0.9
    assert assessment.recommendation == ContinuityRecommendation.CONTINUE
    assert not assessment.discontinuity_reasons
    assert set(assessment.components) >= {"runtime", "checkpoint",
                                          "identity_anchors"}
    assert len(COMPONENTS) == 9


def test_restart_gap_lowers_score():
    monitor = EgoContinuityMonitor()
    clean = monitor.assess({})
    gapped = monitor.assess({"brain_death_gap_seconds": 45.0,
                             "unexpected_deaths": 1})
    assert gapped.continuity_score < clean.continuity_score
    assert any("continuity gap" in r
               for r in gapped.discontinuity_reasons)
    # The wording is operational, never metaphysical.
    assert not any("death" in r and "gap" not in r
                   for r in gapped.discontinuity_reasons
                   if "ungraceful" not in r)
    assert "not metaphysical death" in gapped.note


def test_checkpoint_mismatch_recommends_review():
    monitor = EgoContinuityMonitor()
    assessment = monitor.assess({"restored_from_checkpoint": True,
                                 "checkpoint_verified": False})
    assert assessment.recommendation \
        == ContinuityRecommendation.REQUEST_OPERATOR_REVIEW
    assert "checkpoint_state" in assessment.restored_fields
    assert any("did not verify" in r
               for r in assessment.discontinuity_reasons)


def test_identity_mismatch_recommends_review():
    identity = IdentityState()
    identity.update(ANCHORS)
    identity.update(dict(ANCHORS, run_id="r-OTHER"))
    monitor = EgoContinuityMonitor()
    assessment = monitor.assess({}, identity_state=identity)
    assert assessment.components["identity_anchors"] < 1.0
    assert assessment.recommendation \
        == ContinuityRecommendation.REQUEST_OPERATOR_REVIEW


def test_critical_health_recommends_safe_shutdown():
    monitor = EgoContinuityMonitor()
    assessment = monitor.assess({"health_level": "critical"})
    assert assessment.recommendation \
        == ContinuityRecommendation.SAFE_SHUTDOWN_RECOMMENDED
    # A recommendation only; the monitor has nothing to execute it with.
    assert not hasattr(monitor, "shutdown")


def test_restored_and_missing_fields_tracked():
    monitor = EgoContinuityMonitor()
    assessment = monitor.assess({"inner_map_restored": True,
                                 "world_model_restored": False})
    assert "inner_map_restored" in assessment.restored_fields
    assert any("world_model" in r
               for r in assessment.discontinuity_reasons)
    assert "homeostasis_restored" in assessment.missing_fields
