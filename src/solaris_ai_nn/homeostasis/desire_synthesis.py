"""Desire synthesis -- needs and drives become formal Desire suggestions.

The missing calculus between Stimulus and Desire: need/drive pressure is
converted into ranked :class:`DesireCandidate` objects that map onto the
canonical Solaris ``Desire`` signal. Candidates are suggestions only -- they
execute nothing, blocked candidates stay in the list with their reasons, and
every candidate carries its safety and governance status.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..signals import canonical as C
from .conflict import ConflictResolver, NeedConflict
from .drives import DriveResolver
from .needs import NeedState
from .safety import HomeostasisSafetyValidator
from .variables import clamp01

DESIRE_PROPOSALS = (
    "rest", "look", "seek_signal", "avoid_danger", "approach_reward",
    "consolidate_memory", "run_replay", "request_operator_review",
    "checkpoint_now", "reduce_activity", "explore_safely", "stabilize",
    "remain_observe_only", "safe_shutdown_recommended",
)


@dataclass
class DesireCandidate:
    """One ranked, safety-checked Desire suggestion."""

    proposal: str
    motivation: float = 0.0
    confidence: float = 0.0
    source_needs: List[str] = field(default_factory=list)
    source_drives: List[str] = field(default_factory=list)
    inhibited_by: List[str] = field(default_factory=list)
    safety_status: str = "ok"
    governance_status: str = "ok"
    blocked: bool = False
    blocked_reason: str = ""
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_canonical(self) -> C.Desire:
        """The Solaris-compatible Desire object (a suggestion, never an act)."""
        return C.Desire(origin="homeostasis", proposal=self.proposal,
                        motivation=clamp01(self.motivation),
                        confidence=clamp01(self.confidence))

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class DesireSynthesisEngine:
    """Need/drive state -> ranked Desire candidates."""

    safety: HomeostasisSafetyValidator = field(
        default_factory=HomeostasisSafetyValidator)
    synthesized_total: int = field(default=0, init=False)
    suppressed_total: int = field(default=0, init=False)
    last_candidates: List[DesireCandidate] = field(default_factory=list,
                                                   init=False)

    def synthesize(self, need_state: NeedState,
                   drive_resolver: DriveResolver,
                   conflicts: Optional[List[NeedConflict]] = None,
                   context: Optional[Dict[str, Any]] = None,
                   ) -> List[DesireCandidate]:
        ctx = context or {}
        conflicts = conflicts or []
        suppressed = ConflictResolver().suppressed_desires(conflicts) \
            if conflicts else {}
        bias = drive_resolver.desire_bias()

        # Collect proposals from needs (with intensity) and drive bias.
        votes: Dict[str, Dict[str, Any]] = {}
        for need in need_state.needs:
            for proposal in need.possible_desires:
                vote = votes.setdefault(proposal, {
                    "motivation": 0.0, "needs": [], "drives": [],
                    "inhibited": []})
                vote["motivation"] = max(vote["motivation"], need.intensity)
                vote["needs"].append(need.type)
                vote["inhibited"].extend(need.inhibited_by)
        for category, drive in drive_resolver.state.drives.items():
            if drive.pressure <= 0:
                continue
            from .drives import DRIVE_TO_PROPOSALS

            for proposal in DRIVE_TO_PROPOSALS.get(category, {}):
                if proposal in votes:
                    votes[proposal]["drives"].append(category)
        if ctx.get("safe_shutdown_recommended"):
            votes.setdefault("safe_shutdown_recommended", {
                "motivation": 0.8, "needs": [], "drives": [],
                "inhibited": []})["drives"].append("continuity_drive")

        candidates: List[DesireCandidate] = []
        for proposal in sorted(votes):
            vote = votes[proposal]
            motivation = clamp01(vote["motivation"]
                                 + 0.2 * bias.get(proposal, 0.0))
            candidate = DesireCandidate(
                proposal=proposal,
                motivation=round(motivation, 4),
                confidence=round(min(0.95, 0.3 + 0.15 * len(vote["needs"])
                                     + 0.1 * len(vote["drives"])), 4),
                source_needs=sorted(set(vote["needs"])),
                source_drives=sorted(set(vote["drives"])),
                inhibited_by=sorted(set(vote["inhibited"])))

            # Safety gate: candidates that fail are kept, marked blocked.
            safety_report = self.safety.validate_desire_candidate(
                proposal, ctx)
            if not safety_report.safe:
                candidate.safety_status = "rejected"
                candidate.blocked = True
                candidate.blocked_reason = safety_report.violations[0]
            # Conflict suppression: recorded with the resolver's reason.
            if proposal in suppressed:
                candidate.blocked = True
                candidate.blocked_reason = suppressed[proposal]
                candidate.governance_status = "suppressed_by_conflict"
            # Governance context (e.g. observe-only) can also block.
            if ctx.get("governance_blocks", {}).get(proposal):
                candidate.blocked = True
                candidate.governance_status = "blocked_by_governance"
                candidate.blocked_reason = ctx["governance_blocks"][proposal]
            candidates.append(candidate)

        candidates.sort(key=lambda c: (c.blocked, -c.motivation, c.proposal))
        self.synthesized_total += len(candidates)
        self.suppressed_total += sum(1 for c in candidates if c.blocked)
        self.last_candidates = candidates
        return candidates

    def best(self) -> Optional[DesireCandidate]:
        for candidate in self.last_candidates:
            if not candidate.blocked:
                return candidate
        return None

    def snapshot(self) -> Dict[str, Any]:
        best = self.best()
        return {
            "synthesized_total": self.synthesized_total,
            "suppressed_total": self.suppressed_total,
            "best": best.to_dict() if best else None,
            "last_candidates": [c.to_dict()
                                for c in self.last_candidates[:8]],
            "note": "Desire candidates are suggestions only; nothing here "
                    "executes actions",
        }
