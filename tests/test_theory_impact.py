"""Theory impact: challenged, narrowed, retired with history preserved."""

from __future__ import annotations

from solaris_ai_nn.review_assimilation import (
    ObjectionValidityStatus,
    ReviewerObjectionClassifier,
    TheoryImpactAssessor,
    TheoryImpactType,
)


def _classify(objections):
    return ReviewerObjectionClassifier().classify(objections)


def test_theory_challenged():
    objs = _classify([
        {"objection_id": "o1", "text": "Could be a passive parser artifact.",
         "claim_refs": ["c1"]}])
    impacts = TheoryImpactAssessor().assess(
        objections=objs, theory_links={"o1": "t1"})
    assert any(i.impact_type == TheoryImpactType.CHALLENGE_WORKING_HYPOTHESIS
               for i in impacts)
    assert impacts[0].theory_id == "t1"


def test_theory_narrowed():
    objs = _classify([
        {"objection_id": "o1", "text": "Probably fixture overfit."}])
    impacts = TheoryImpactAssessor().assess(objections=objs)
    assert any(i.impact_type == TheoryImpactType.NARROW_THEORY_SCOPE
               for i in impacts)


def test_theory_accepted_falsification():
    objs = _classify([
        {"objection_id": "o1", "text": "passive parser equivalent",
         "validity": ObjectionValidityStatus.ACCEPTED_AS_FALSIFICATION}])
    impacts = TheoryImpactAssessor().assess(objections=objs)
    assert any(i.impact_type == TheoryImpactType.ACCEPTED_FALSIFICATION
               for i in impacts)


def test_preserves_prior_statements():
    objs = _classify([{"objection_id": "o1", "text": "fixture overfit"}])
    impacts = TheoryImpactAssessor().assess(objections=objs)
    assert all(i.to_dict()["preserves_prior_statements"] is True
               for i in impacts)
    assert all(i.to_dict()["proves_consciousness"] is False for i in impacts)


def test_summary_revision_count():
    objs = _classify([
        {"objection_id": "o1", "text": "passive parser artifact"},
        {"objection_id": "o2", "text": "fixture overfit"}])
    impacts = TheoryImpactAssessor().assess(objections=objs)
    summary = TheoryImpactAssessor.summary(impacts)
    assert summary["theory_revision_count"] >= 1
