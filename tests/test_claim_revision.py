"""Claim revision: safe wording generated, unsafe blocked, no registry edit."""

from __future__ import annotations

from solaris_ai_nn.review_assimilation import (
    ClaimImpactAssessment,
    ClaimImpactType,
    ClaimRevisionProposer,
    ClaimRevisionStatus,
    ClaimRevisionType,
)


def test_safe_wording_generated():
    impacts = [ClaimImpactAssessment(
        claim_id="c1", impact_type=ClaimImpactType.DOWNGRADE_TO_WEAK)]
    proposals = ClaimRevisionProposer().propose(
        impacts=impacts, claim_text_by_id={"c1": "the architecture forms signs"})
    p = proposals[0]
    assert p.revision_type == ClaimRevisionType.DOWNGRADE_STRENGTH
    assert "weakly supported" in p.proposed_wording
    # Safe wording still includes limitations.
    assert "no claim of consciousness" in p.proposed_wording.lower()


def test_unsafe_wording_blocked():
    # A claim text containing forbidden wording would fail ClaimGuard; the
    # mark_forbidden proposal text is itself a disclaimer (safe). Force an
    # unsafe original to confirm the guard path.
    impacts = [ClaimImpactAssessment(
        claim_id="c1", impact_type=ClaimImpactType.DOWNGRADE_TO_WEAK)]
    proposals = ClaimRevisionProposer().propose(
        impacts=impacts,
        claim_text_by_id={"c1": "the system is conscious and feels joy"})
    p = proposals[0]
    # The proposed wording embeds the unsafe original -> ClaimGuard blocks it.
    assert p.status == ClaimRevisionStatus.BLOCKED_UNSAFE_WORDING
    assert "blocked by ClaimGuard" in p.proposed_wording


def test_revision_does_not_edit_registry():
    impacts = [ClaimImpactAssessment(
        claim_id="c1", impact_type=ClaimImpactType.MARK_UNSUPPORTED)]
    proposals = ClaimRevisionProposer().propose(impacts=impacts)
    assert all(p.to_dict()["edits_registry"] is False for p in proposals)
    assert all(p.to_dict()["is_proposal"] is True for p in proposals)


def test_operator_review_status():
    impacts = [ClaimImpactAssessment(
        claim_id="c1", impact_type=ClaimImpactType.DOWNGRADE_TO_WEAK)]
    proposals = ClaimRevisionProposer(require_operator_review=True).propose(
        impacts=impacts, claim_text_by_id={"c1": "a bounded result"})
    assert proposals[0].status == ClaimRevisionStatus.REQUIRES_OPERATOR_REVIEW
