"""Arbitration -- competing candidates scored with every component visible.

Fourteen score components combine into one total per candidate, with the
structural rule that safety/governance/inhibition penalties dominate: each
carries a -10.0 weight against utility components bounded in [0, 1], so a
forbidden candidate can never out-score a safe one. When nothing safe
remains, the arbitrator falls back to ``no_action`` or
``request_operator_review`` -- it never forces a choice.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .action_candidates import (
    ActionCandidate,
    ActionCandidateType,
    no_action_candidate,
)

# Penalty weight that structurally dominates all utility components.
BLOCKING_PENALTY = 10.0

SCORE_COMPONENTS = (
    "need_pressure", "drive_priority", "urgency", "confidence",
    "expected_valence", "expected_risk", "expected_energy_cost",
    "world_model_support", "habit_support", "novelty_pressure",
    "safety_penalty", "governance_penalty", "inhibition_penalty",
    "operational_health_penalty",
)


@dataclass
class ArbitrationScore:
    """One candidate's full score breakdown."""

    candidate: ActionCandidate
    components: Dict[str, float] = field(default_factory=dict)
    total: float = 0.0
    blocked: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.candidate.label,
            "action_type": self.candidate.action_type,
            "components": dict(self.components),
            "total": round(self.total, 6),
            "blocked": self.blocked,
        }


@dataclass
class ArbitrationResult:
    """The selection plus the entire ranked field."""

    selected: Optional[ActionCandidate]
    scores: List[ArbitrationScore] = field(default_factory=list)
    reason: str = ""
    fallback_used: bool = False
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "selected": (self.selected.to_dict()
                         if self.selected else None),
            "scores": [s.to_dict() for s in self.scores],
            "reason": self.reason,
            "fallback_used": self.fallback_used,
            "timestamp": self.timestamp,
        }


@dataclass
class ActionArbitrator:
    """Scores and selects among action candidates."""

    selections_total: int = field(default=0, init=False)
    fallback_total: int = field(default=0, init=False)
    last_result: Optional[ArbitrationResult] = field(default=None,
                                                     init=False)

    def score_candidate(self, candidate: ActionCandidate,
                        context: Optional[Dict[str, Any]] = None,
                        ) -> ArbitrationScore:
        ctx = context or {}
        meta = candidate.metadata or {}
        needs = meta.get("source_needs", [])
        drives = meta.get("source_drives", [])
        drive_priorities = ctx.get("drive_priorities") or {}
        world_support = (ctx.get("world_model_support") or {}).get(
            candidate.label, 0.0)
        habit_support = (ctx.get("habit_support") or {}).get(
            candidate.label, 0.0)
        prospection = (ctx.get("prospection") or {}).get(
            candidate.label, {})

        components = {
            "need_pressure": round(min(1.0, candidate.utility_estimate), 4),
            "drive_priority": round(max(
                [drive_priorities.get(d, 0.0) for d in drives] or [0.0]), 4),
            "urgency": round(float(meta.get("urgency",
                                            candidate.utility_estimate)
                                   or 0.0), 4),
            "confidence": round(candidate.confidence * 0.5, 4),
            "expected_valence": round(float(
                prospection.get("expected_valence", 0.0) or 0.0) * 0.8, 4),
            "expected_risk": round(-abs(candidate.expected_risk), 4),
            "expected_energy_cost": round(-abs(candidate.expected_cost)
                                          * 0.5, 4),
            "world_model_support": round(min(1.0, world_support) * 0.5, 4),
            "habit_support": round(min(1.0, habit_support) * 0.3, 4),
            "novelty_pressure": round(
                0.3 * float(ctx.get("mysterium_pressure", 0.0) or 0.0)
                if candidate.label in ("run_replay", "explore_safely",
                                       "look") else 0.0, 4),
            "safety_penalty": (-BLOCKING_PENALTY
                               if candidate.safety_status != "ok" else 0.0),
            "governance_penalty": (-BLOCKING_PENALTY
                                   if candidate.governance_status
                                   not in ("ok", "")
                                   else 0.0),
            "inhibition_penalty": (-BLOCKING_PENALTY
                                   if candidate.inhibited else 0.0),
            "operational_health_penalty": (
                -0.5 if ctx.get("health_level") == "warning"
                and candidate.expected_cost > 0.1
                else -BLOCKING_PENALTY
                if ctx.get("health_level") == "critical"
                and candidate.action_type in (
                    ActionCandidateType.SIMULATED_EMBODIED_ACTION,
                    ActionCandidateType.SIDECAR_SUGGESTION)
                else 0.0),
        }
        total = sum(components.values())
        blocked = any(components[key] <= -BLOCKING_PENALTY for key in
                      ("safety_penalty", "governance_penalty",
                       "inhibition_penalty",
                       "operational_health_penalty"))
        return ArbitrationScore(candidate=candidate, components=components,
                                total=total, blocked=blocked)

    def rank_candidates(self, candidates: List[ActionCandidate],
                        context: Optional[Dict[str, Any]] = None,
                        ) -> List[ArbitrationScore]:
        scores = [self.score_candidate(c, context) for c in candidates]
        scores.sort(key=lambda s: (s.blocked, -s.total, s.candidate.label))
        return scores

    def select(self, candidates: List[ActionCandidate],
               context: Optional[Dict[str, Any]] = None,
               ) -> ArbitrationResult:
        ctx = context or {}
        scores = self.rank_candidates(candidates, ctx)
        viable = [s for s in scores if not s.blocked]
        if viable:
            best = viable[0]
            dominant = max((k for k in best.components
                            if not k.endswith("_penalty")),
                           key=lambda k: best.components[k])
            result = ArbitrationResult(
                selected=best.candidate, scores=scores,
                reason=(f"highest total ({best.total:.3f}) among safe "
                        f"candidates; dominant component: {dominant} "
                        f"({best.components[dominant]:.3f})"))
        else:
            # Nothing safe: fall back, never force.
            review = [c for c in candidates if c.action_type
                      == ActionCandidateType.OPERATOR_REVIEW_REQUEST
                      and not c.inhibited]
            fallback = (review[0] if review
                        else no_action_candidate(
                            "no safe candidate survived arbitration"))
            result = ArbitrationResult(
                selected=fallback, scores=scores, fallback_used=True,
                reason="no candidate passed safety/governance/inhibition; "
                       "fell back to "
                       f"{fallback.label!r}")
            self.fallback_total += 1
        self.selections_total += 1
        self.last_result = result
        return result

    def snapshot(self) -> Dict[str, Any]:
        return {
            "selections_total": self.selections_total,
            "fallback_total": self.fallback_total,
            "score_components": list(SCORE_COMPONENTS),
            "last": (self.last_result.to_dict()
                     if self.last_result else None),
        }
