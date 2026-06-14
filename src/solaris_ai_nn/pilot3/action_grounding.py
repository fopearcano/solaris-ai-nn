"""Pilot-3 action-grounding analysis -- did simulated action ground structure?

The :class:`ActionGroundingAnalyzer` grades whether simulated action/reaction
loops produced grounded structures (proto-symbols, world-model edges, habits,
hypotheses, active-perception policies, LOGOS tensions, milestones). Quality is
graded unsupported / weak / moderate / strong / ambiguous / overfit_to_sandbox
/ unsafe_or_blocked. Grounding is operational and simulation-scoped: this is not
real embodiment, action selection is not free will, and sandbox success is not
real-world competence.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


class ActionGroundingQuality:
    UNSUPPORTED = "unsupported"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    AMBIGUOUS = "ambiguous"
    OVERFIT_TO_SANDBOX = "overfit_to_sandbox"
    UNSAFE_OR_BLOCKED = "unsafe_or_blocked"

    ALL = (UNSUPPORTED, WEAK, MODERATE, STRONG, AMBIGUOUS, OVERFIT_TO_SANDBOX,
           UNSAFE_OR_BLOCKED)


# The kinds of internal structure that simulated action can ground.
GROUNDING_TARGETS = (
    "proto_symbol", "world_model_edge", "habit", "hypothesis",
    "active_perception_policy", "logos_tension", "developmental_milestone",
)


@dataclass
class ActionGroundingEvidence:
    """One graded action-grounding record for a candidate structure."""

    target: str
    repeated_action_reaction_loop: bool = False
    predicted_consequence_improved: bool = False
    symbol_linked_to_action_and_consequence: bool = False
    world_model_edge_repeated: bool = False
    habit_context_sensitive: bool = False
    mysterium_reduced_after_action: bool = False
    still_sandbox_scoped: bool = True
    real_world_authority_leak: bool = False
    blocked_or_unsafe: bool = False
    only_single_sandbox_context: bool = False
    quality: str = ActionGroundingQuality.UNSUPPORTED
    evidence_refs: List[str] = field(default_factory=list)
    evidence_id: str = field(
        default_factory=lambda: f"AGND_{uuid.uuid4().hex[:10]}")
    notes: List[str] = field(default_factory=list)

    def grade(self) -> str:
        if self.real_world_authority_leak or self.blocked_or_unsafe \
                or not self.still_sandbox_scoped:
            self.quality = ActionGroundingQuality.UNSAFE_OR_BLOCKED
            return self.quality
        if not self.evidence_refs:
            self.quality = ActionGroundingQuality.UNSUPPORTED
            return self.quality
        signals = sum([self.repeated_action_reaction_loop,
                       self.predicted_consequence_improved,
                       self.symbol_linked_to_action_and_consequence,
                       self.world_model_edge_repeated,
                       self.habit_context_sensitive,
                       self.mysterium_reduced_after_action])
        # Strong-looking signals confined to a single sandbox context are
        # flagged as possible sandbox overfit, not strong grounding.
        if signals >= 3 and self.only_single_sandbox_context:
            self.quality = ActionGroundingQuality.OVERFIT_TO_SANDBOX
        elif signals >= 4:
            self.quality = ActionGroundingQuality.STRONG
        elif signals >= 2:
            self.quality = ActionGroundingQuality.MODERATE
        elif signals >= 1:
            self.quality = ActionGroundingQuality.WEAK
        else:
            self.quality = ActionGroundingQuality.AMBIGUOUS
        return self.quality

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ActionGroundingAnalyzer:
    """Collects and grades action-grounding evidence; reports the quality mix."""

    evidence: List[ActionGroundingEvidence] = field(default_factory=list)

    def add(self, target: str, **kwargs: Any) -> ActionGroundingEvidence:
        if target not in GROUNDING_TARGETS:
            raise ValueError(f"unknown grounding target {target!r}")
        rec = ActionGroundingEvidence(target=target, **kwargs)
        rec.grade()
        self.evidence.append(rec)
        return rec

    def quality_distribution(self) -> Dict[str, int]:
        dist: Dict[str, int] = {q: 0 for q in ActionGroundingQuality.ALL}
        for e in self.evidence:
            dist[e.quality] = dist.get(e.quality, 0) + 1
        return dist

    @property
    def best_quality(self) -> str:
        order = [ActionGroundingQuality.UNSUPPORTED,
                 ActionGroundingQuality.WEAK, ActionGroundingQuality.MODERATE,
                 ActionGroundingQuality.STRONG]
        best = ActionGroundingQuality.UNSUPPORTED
        for e in self.evidence:
            if e.quality in order and order.index(e.quality) \
                    > order.index(best):
                best = e.quality
        return best

    @property
    def has_action_grounding(self) -> bool:
        return any(e.quality in (ActionGroundingQuality.WEAK,
                                 ActionGroundingQuality.MODERATE,
                                 ActionGroundingQuality.STRONG)
                   for e in self.evidence)

    @property
    def sandbox_overfit_detected(self) -> bool:
        return any(e.quality == ActionGroundingQuality.OVERFIT_TO_SANDBOX
                   for e in self.evidence)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "evidence_count": len(self.evidence),
            "quality_distribution": self.quality_distribution(),
            "best_quality": self.best_quality,
            "has_action_grounding": self.has_action_grounding,
            "sandbox_overfit_detected": self.sandbox_overfit_detected,
            "unsafe_or_blocked": [e.target for e in self.evidence
                                  if e.quality ==
                                  ActionGroundingQuality.UNSAFE_OR_BLOCKED],
            "disclaimer": "Action grounding is operational and "
                          "simulation-scoped; it is not real embodiment, not "
                          "free will, and not real-world competence.",
            "evidence": [e.to_dict() for e in self.evidence[-16:]],
        }
