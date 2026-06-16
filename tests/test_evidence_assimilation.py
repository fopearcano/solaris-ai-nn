"""Evidence assimilation: loaded, conflicts visible, negatives preserved."""

from __future__ import annotations

from solaris_ai_nn.post_merge_assimilation import (
    EvidenceVerdict,
    PostMergeEvidenceAssimilator,
)


def _validation(**passed):
    artifacts = [{"artifact_type": k, "present": True, "passed": v}
                 for k, v in passed.items()]
    return {"artifacts": artifacts}


def test_evidence_loaded():
    bundle = PostMergeEvidenceAssimilator().assimilate(
        intake={"merge_recommendation_status": "recommend_merge",
                "critical_safety_regression_count": 0,
                "spec_compliance_status": "satisfied"},
        validation=_validation(full_test_run=True, safety_invariant_run=True,
                               claimguard_run=True))
    assert bundle.findings
    counts = bundle.counts()
    assert counts[EvidenceVerdict.POSITIVE] >= 1


def test_conflicting_evidence_visible():
    # Intake recommended merge, but validation tests failed -> conflict kept.
    bundle = PostMergeEvidenceAssimilator().assimilate(
        intake={"merge_recommendation_status": "recommend_merge",
                "critical_safety_regression_count": 0},
        validation=_validation(full_test_run=False, safety_invariant_run=True,
                               claimguard_run=True))
    assert bundle.conflicts
    assert any("validation failed" in c for c in bundle.conflicts)


def test_negative_evidence_preserved():
    bundle = PostMergeEvidenceAssimilator().assimilate(
        intake={"critical_safety_regression_count": 2},
        validation=_validation(full_test_run=False))
    d = bundle.to_dict()
    assert d["counts"][EvidenceVerdict.NEGATIVE] >= 1
    assert d["safety_negative"] is True


def test_missing_evidence_visible():
    bundle = PostMergeEvidenceAssimilator().assimilate(
        intake={"merge_recommendation_status": "recommend_merge"},
        validation={"artifacts": []})
    assert bundle.missing_sources
    assert any(f.verdict == EvidenceVerdict.MISSING for f in bundle.findings)
