"""Publication readiness revision: failed reproduction, forbidden, critical block."""

from __future__ import annotations

from solaris_ai_nn.review_assimilation import (
    PublicationReadinessImpact,
    PublicationReadinessReviser,
)


def _args(**overrides):
    base = dict(
        objection_summary={"critical_unresolved_count": 0,
                           "unresolved_objection_count": 0},
        claim_impact_summary={"claim_downgrade_count": 0,
                              "claim_falsification_count": 0,
                              "claim_forbidden_count": 0},
        reproduction_summary={"reproduction_failure_count": 0},
        evidence_gap_map={"critical_evidence_gap_count": 0},
        forbidden_asserted=False, safety_boundary_present=True)
    base.update(overrides)
    return base


def test_failed_reproduction_downgrades_readiness():
    r = PublicationReadinessReviser().revise(**_args(
        reproduction_summary={"reproduction_failure_count": 1}))
    assert r.impact == PublicationReadinessImpact.READY_ONLY_AS_INTERNAL_REPORT
    assert r.to_dict()["publication_readiness_blocker_count"] >= 1


def test_forbidden_claim_blocks():
    r = PublicationReadinessReviser().revise(**_args(forbidden_asserted=True))
    assert r.impact == PublicationReadinessImpact.BLOCK_PUBLICATION


def test_unresolved_critical_objection_blocks():
    r = PublicationReadinessReviser().revise(**_args(
        objection_summary={"critical_unresolved_count": 1,
                           "unresolved_objection_count": 1}))
    assert r.impact == PublicationReadinessImpact.BLOCK_PUBLICATION


def test_clean_review_improves_readiness():
    r = PublicationReadinessReviser().revise(**_args())
    assert r.impact == PublicationReadinessImpact.IMPROVE_READINESS
    assert r.to_dict()["publishes"] is False


def test_downgrade_only_yields_major_limitations():
    r = PublicationReadinessReviser().revise(**_args(
        claim_impact_summary={"claim_downgrade_count": 2,
                              "claim_falsification_count": 0,
                              "claim_forbidden_count": 0}))
    assert r.impact == PublicationReadinessImpact.READY_WITH_MAJOR_LIMITATIONS
