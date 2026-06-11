"""Ego continuity monitor -- how unbroken is the runtime thread?

Nine continuity components (runtime, checkpoint, anchors, Inner MAP, world
model, need/drive, executive trace, latent memory, pilot/sidecar) are each
scored from concrete context facts and combined into one continuity score
with discontinuity reasons, restored/missing fields, and a recommendation.
A discontinuity is a *runtime continuity gap* -- never described as death
outside of documented Solaris_Ai terminology.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ContinuityRecommendation:
    CONTINUE = "continue"
    CHECKPOINT_NOW = "checkpoint_now"
    REQUEST_OPERATOR_REVIEW = "request_operator_review"
    MARK_IDENTITY_UNCERTAIN = "mark_identity_uncertain"
    SAFE_SHUTDOWN_RECOMMENDED = "safe_shutdown_recommended"

    ALL = (CONTINUE, CHECKPOINT_NOW, REQUEST_OPERATOR_REVIEW,
           MARK_IDENTITY_UNCERTAIN, SAFE_SHUTDOWN_RECOMMENDED)


COMPONENTS = (
    "runtime", "checkpoint", "identity_anchors", "inner_map",
    "world_model", "need_drive", "executive_trace", "latent_memory",
    "pilot_sidecar",
)

CONTINUITY_NOTE = ("a discontinuity is a runtime continuity gap, an "
                   "operational fact -- not metaphysical death")


@dataclass
class ContinuityAssessment:
    """One continuity reading across the nine components."""

    continuity_score: float = 1.0
    components: Dict[str, float] = field(default_factory=dict)
    discontinuity_reasons: List[str] = field(default_factory=list)
    restored_fields: List[str] = field(default_factory=list)
    missing_fields: List[str] = field(default_factory=list)
    recommendation: str = ContinuityRecommendation.CONTINUE
    note: str = CONTINUITY_NOTE
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class EgoContinuityMonitor:
    """Scores continuity from context facts; recommends, never acts."""

    assessments_made: int = field(default=0, init=False)
    last_assessment: Optional[ContinuityAssessment] = field(default=None,
                                                            init=False)

    def assess(self, context: Optional[Dict[str, Any]] = None,
               identity_state: Optional[Any] = None,
               ) -> ContinuityAssessment:
        ctx = dict(context or {})
        components: Dict[str, float] = {}
        reasons: List[str] = []
        restored: List[str] = []
        missing: List[str] = []

        # Runtime: heartbeat freshness and no unexpected deaths.
        gap = float(ctx.get("brain_death_gap_seconds", 0.0) or 0.0)
        deaths = int(ctx.get("unexpected_deaths", 0) or 0)
        runtime = max(0.0, 1.0 - min(1.0, gap / 60.0) - 0.3 * deaths)
        components["runtime"] = round(runtime, 4)
        if gap > 5.0:
            reasons.append(f"runtime continuity gap of {gap:.1f}s between "
                           "sessions")
        if deaths:
            reasons.append(f"{deaths} ungraceful session end(s) recorded")

        # Checkpoint: was one restored, and does it verify?
        if ctx.get("restored_from_checkpoint"):
            restored.append("checkpoint_state")
            ok = ctx.get("checkpoint_verified", True)
            components["checkpoint"] = 0.9 if ok else 0.3
            if not ok:
                reasons.append("the restored checkpoint did not verify "
                               "cleanly")
        else:
            components["checkpoint"] = (1.0 if ctx.get("fresh_start", True)
                                        else 0.5)

        # Identity anchors.
        if identity_state is not None:
            components["identity_anchors"] = round(
                float(getattr(identity_state, "continuity_score", 1.0)), 4)
            if getattr(identity_state, "mismatch_count", 0) > 0:
                reasons.append("identity anchors mismatch a previous "
                               "session; runtime continuity is uncertain")
        else:
            components["identity_anchors"] = float(
                ctx.get("identity_continuity", 1.0) or 1.0)

        # Module continuity: restored vs missing persisted fields.
        for component, key in (("inner_map", "inner_map_restored"),
                               ("world_model", "world_model_restored"),
                               ("need_drive", "homeostasis_restored"),
                               ("executive_trace", "executive_restored"),
                               ("latent_memory", "latent_restored"),
                               ("pilot_sidecar", "sidecar_continuity")):
            value = ctx.get(key)
            if value is None:
                components[component] = 1.0  # not in use: nothing broken
                missing.append(key)
            elif bool(value):
                components[component] = 1.0
                restored.append(key)
            else:
                components[component] = 0.4
                reasons.append(f"{component} state was expected but not "
                               "restored")

        score = round(sum(components.values()) / len(components), 4)
        recommendation = self._recommend(score, reasons, ctx)
        assessment = ContinuityAssessment(
            continuity_score=score, components=components,
            discontinuity_reasons=reasons, restored_fields=restored,
            missing_fields=missing, recommendation=recommendation)
        self.assessments_made += 1
        self.last_assessment = assessment
        return assessment

    @staticmethod
    def _recommend(score: float, reasons: List[str],
                   ctx: Dict[str, Any]) -> str:
        if ctx.get("health_level") == "critical":
            return ContinuityRecommendation.SAFE_SHUTDOWN_RECOMMENDED
        if any("did not verify" in r or "mismatch" in r for r in reasons):
            return ContinuityRecommendation.REQUEST_OPERATOR_REVIEW
        if score < 0.5:
            return ContinuityRecommendation.MARK_IDENTITY_UNCERTAIN
        if score < 0.8:
            return ContinuityRecommendation.CHECKPOINT_NOW
        return ContinuityRecommendation.CONTINUE

    def snapshot(self) -> Dict[str, Any]:
        return {
            "assessments_made": self.assessments_made,
            "last": (self.last_assessment.to_dict()
                     if self.last_assessment else None),
            "components": list(COMPONENTS),
            "note": CONTINUITY_NOTE,
        }
