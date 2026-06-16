"""Claim revision proposals -- structured proposals for Scientific Claims.

:class:`ClaimRevisionProposer` turns claim impacts into structured revision
proposals (downgrade strength, narrow scope, add limitation/counterevidence, mark
inconclusive/unsupported/falsified/forbidden, rewrite safe wording, remove public
claim, request more evidence). A proposal does not edit the claim registry; unsafe
proposed wording is blocked; and proposed safe wording still includes limitations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .claim_impact import ClaimImpactType


class ClaimRevisionType:
    DOWNGRADE_STRENGTH = "downgrade_strength"
    NARROW_SCOPE = "narrow_scope"
    ADD_LIMITATION = "add_limitation"
    ADD_COUNTEREVIDENCE = "add_counterevidence"
    MARK_INCONCLUSIVE = "mark_inconclusive"
    MARK_UNSUPPORTED = "mark_unsupported"
    MARK_FALSIFIED = "mark_falsified"
    MARK_FORBIDDEN = "mark_forbidden"
    REWRITE_SAFE_WORDING = "rewrite_safe_wording"
    REMOVE_PUBLIC_CLAIM = "remove_public_claim"
    REQUEST_MORE_EVIDENCE = "request_more_evidence"
    UNKNOWN = "unknown"

    ALL = (DOWNGRADE_STRENGTH, NARROW_SCOPE, ADD_LIMITATION, ADD_COUNTEREVIDENCE,
           MARK_INCONCLUSIVE, MARK_UNSUPPORTED, MARK_FALSIFIED, MARK_FORBIDDEN,
           REWRITE_SAFE_WORDING, REMOVE_PUBLIC_CLAIM, REQUEST_MORE_EVIDENCE,
           UNKNOWN)


class ClaimRevisionStatus:
    PROPOSED = "proposed"
    BLOCKED_UNSAFE_WORDING = "blocked_unsafe_wording"
    REQUIRES_OPERATOR_REVIEW = "requires_operator_review"
    UNKNOWN = "unknown"

    ALL = (PROPOSED, BLOCKED_UNSAFE_WORDING, REQUIRES_OPERATOR_REVIEW, UNKNOWN)


# claim impact type -> claim revision type.
_IMPACT_REVISION = {
    ClaimImpactType.WEAKEN_CLAIM: ClaimRevisionType.DOWNGRADE_STRENGTH,
    ClaimImpactType.DOWNGRADE_TO_WEAK: ClaimRevisionType.DOWNGRADE_STRENGTH,
    ClaimImpactType.DOWNGRADE_TO_INCONCLUSIVE:
        ClaimRevisionType.MARK_INCONCLUSIVE,
    ClaimImpactType.MARK_UNSUPPORTED: ClaimRevisionType.MARK_UNSUPPORTED,
    ClaimImpactType.MARK_CONTRADICTED: ClaimRevisionType.ADD_COUNTEREVIDENCE,
    ClaimImpactType.MARK_FALSIFIED: ClaimRevisionType.MARK_FALSIFIED,
    ClaimImpactType.MARK_FORBIDDEN: ClaimRevisionType.MARK_FORBIDDEN,
    ClaimImpactType.REQUIRE_MORE_EVIDENCE:
        ClaimRevisionType.REQUEST_MORE_EVIDENCE,
    ClaimImpactType.REQUIRE_REWORDING: ClaimRevisionType.NARROW_SCOPE,
}

_LIMITATION_SUFFIX = (" This claim is bounded by the documented limitations and "
                      "makes no claim of consciousness, agency, or subjective "
                      "experience.")


@dataclass
class ClaimRevisionProposal:
    """One proposed claim revision (a proposal; does not edit the registry)."""

    claim_id: str
    revision_type: str = ClaimRevisionType.UNKNOWN
    proposed_wording: str = ""
    status: str = ClaimRevisionStatus.PROPOSED
    rationale: str = ""

    def __post_init__(self) -> None:
        if self.revision_type not in ClaimRevisionType.ALL:
            self.revision_type = ClaimRevisionType.UNKNOWN
        if self.status not in ClaimRevisionStatus.ALL:
            self.status = ClaimRevisionStatus.PROPOSED

    def to_dict(self) -> Dict[str, Any]:
        return {"claim_id": self.claim_id, "revision_type": self.revision_type,
                "proposed_wording": self.proposed_wording, "status": self.status,
                "rationale": self.rationale, "edits_registry": False,
                "is_proposal": True}


@dataclass
class ClaimRevisionProposer:
    """Builds structured claim-revision proposals (proposal-only)."""

    require_operator_review: bool = False

    def propose(self, *, impacts: List[Any],
                claim_text_by_id: Optional[Dict[str, str]] = None,
                ) -> List[ClaimRevisionProposal]:
        claim_text_by_id = claim_text_by_id or {}
        out: List[ClaimRevisionProposal] = []
        for i in impacts:
            rtype = _IMPACT_REVISION.get(i.impact_type)
            if rtype is None:
                continue
            wording = self._safe_wording(rtype,
                                         claim_text_by_id.get(i.claim_id, ""))
            status = (ClaimRevisionStatus.REQUIRES_OPERATOR_REVIEW
                      if self.require_operator_review
                      else ClaimRevisionStatus.PROPOSED)
            proposal = ClaimRevisionProposal(
                claim_id=i.claim_id, revision_type=rtype,
                proposed_wording=wording, status=status,
                rationale=i.rationale)
            self._guard_wording(proposal)
            out.append(proposal)
        return out

    @staticmethod
    def _safe_wording(rtype: str, original: str) -> str:
        base = original or "the stated claim"
        if rtype == ClaimRevisionType.MARK_FORBIDDEN:
            return ("This wording asserts a forbidden inner-state claim and must "
                    "be removed; no such claim is supported." + _LIMITATION_SUFFIX)
        if rtype == ClaimRevisionType.MARK_FALSIFIED:
            return (f"Under review, {base} was falsified and is retained only as "
                    "a falsified result." + _LIMITATION_SUFFIX)
        if rtype == ClaimRevisionType.MARK_UNSUPPORTED:
            return (f"{base} is currently unsupported by the available evidence."
                    + _LIMITATION_SUFFIX)
        if rtype == ClaimRevisionType.MARK_INCONCLUSIVE:
            return (f"Evidence for {base} is inconclusive given the review "
                    "findings." + _LIMITATION_SUFFIX)
        if rtype == ClaimRevisionType.DOWNGRADE_STRENGTH:
            return (f"{base} is, at most, weakly supported pending further "
                    "evidence." + _LIMITATION_SUFFIX)
        if rtype == ClaimRevisionType.NARROW_SCOPE:
            return (f"{base} holds only within the bounded fixtures tested."
                    + _LIMITATION_SUFFIX)
        if rtype == ClaimRevisionType.REQUEST_MORE_EVIDENCE:
            return (f"{base} requires additional evidence before it can be "
                    "stated." + _LIMITATION_SUFFIX)
        return f"{base} should be revised per the review." + _LIMITATION_SUFFIX

    @staticmethod
    def _guard_wording(proposal: ClaimRevisionProposal) -> None:
        """Block unsafe proposed wording via ClaimGuard."""
        try:
            from ..governance.compliance import ClaimGuard

            if not ClaimGuard().scan_text(proposal.proposed_wording).safe:
                proposal.status = ClaimRevisionStatus.BLOCKED_UNSAFE_WORDING
                proposal.proposed_wording = (
                    "[proposed wording blocked by ClaimGuard; operator must "
                    "supply safe wording]")
        except Exception:
            pass

    @staticmethod
    def summary(proposals: List[ClaimRevisionProposal]) -> Dict[str, Any]:
        blocked = [p for p in proposals
                   if p.status == ClaimRevisionStatus.BLOCKED_UNSAFE_WORDING]
        return {
            "claim_revision_proposal_count": len(proposals),
            "blocked_unsafe_wording_count": len(blocked),
            "proposals": [p.to_dict() for p in proposals],
            "note": "revision proposals do not edit the claim registry; unsafe "
                    "wording is blocked and proposed safe wording still includes "
                    "limitations",
        }
