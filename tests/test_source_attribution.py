"""SourceAttributionEngine: evidence preserved; corruption warned; gloss not evidence."""

from __future__ import annotations

from solaris_ai_nn.self_boundary import (
    AttributionEvidence,
    AttributionTarget,
    SourceAttributionEngine,
)


def test_source_evidence_preserved():
    engine = SourceAttributionEngine()
    att = engine.attribute(AttributionTarget.EXTERNAL_SOURCE, "rf_src",
                           confidence=0.7,
                           evidence=[AttributionEvidence(kind="feature",
                                                         detail="rf power")])
    assert att.target == AttributionTarget.EXTERNAL_SOURCE
    assert att.evidence and att.evidence[0].kind == "feature"


def test_corrupted_source_warning():
    engine = SourceAttributionEngine()
    att = engine.attribute(AttributionTarget.EXTERNAL_SOURCE, "bad_src",
                           confidence=0.9, corrupted=True)
    # A corrupted source is never promoted to internal truth.
    assert att.target == AttributionTarget.CORRUPTED_SOURCE
    assert att.confidence <= 0.3
    assert len(engine.corrupted()) == 1


def test_gloss_not_evidence():
    engine = SourceAttributionEngine()
    att = engine.attribute_gloss("gloss_ref")
    assert att.target == AttributionTarget.HUMAN_ANNOTATION
    assert att.gloss_is_not_evidence is True
    assert "gloss is not source evidence" in att.to_dict()["note"]


def test_uncertainty_score():
    engine = SourceAttributionEngine()
    engine.attribute(AttributionTarget.EXTERNAL_SOURCE, "s1", confidence=0.5)
    assert 0.0 <= engine.uncertainty_score() <= 1.0
