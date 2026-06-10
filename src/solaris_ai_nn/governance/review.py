"""Post-run review -- a human-readable account and a recommendation, no more.

The review aggregates what happened (incidents, violations, approvals,
scores, plasticity changes, emergency stops) and recommends what to do next.
It never escalates automatically: the recommendation is a string for a human
to read, not a trigger.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class NextRunRecommendation:
    REPEAT = "repeat"
    EXTEND_DURATION = "extend_duration"
    REDUCE_SCOPE = "reduce_scope"
    INVESTIGATE_FAILURE = "investigate_failure"
    STOP_LINE_OF_WORK = "stop_line_of_work"

    ALL = (REPEAT, EXTEND_DURATION, REDUCE_SCOPE, INVESTIGATE_FAILURE,
           STOP_LINE_OF_WORK)


@dataclass
class ReviewRecord:
    """One finished review (serializable)."""

    run_id: str
    reviewer: str = ""
    recommendation: str = NextRunRecommendation.REPEAT
    recommendation_reasons: List[str] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)
    review_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if self.recommendation not in NextRunRecommendation.ALL:
            raise ValueError(
                f"unknown recommendation {self.recommendation!r}")

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)

    def to_markdown(self) -> str:
        lines = [f"# Post-run review: {self.run_id}", "",
                 f"Reviewer: {self.reviewer or 'unassigned'}",
                 f"Recommendation: **{self.recommendation}** (a "
                 "recommendation for a human, never an automatic action)",
                 ""]
        for reason in self.recommendation_reasons:
            lines.append(f"- {reason}")
        lines.append("")
        for key, value in self.summary.items():
            lines.append(f"- **{key}**: {value}")
        if self.notes:
            lines.append("")
            lines.append("## Notes")
            lines.extend(f"- {n}" for n in self.notes)
        lines.append("")
        return "\n".join(lines)


@dataclass
class PostRunReview:
    """Builds a ReviewRecord from the run's evidence."""

    run_id: str
    reviewer: str = ""

    def build(self,
              status: Optional[Dict[str, Any]] = None,
              incidents: Optional[List[Dict[str, Any]]] = None,
              policy_violations: Optional[List[Dict[str, Any]]] = None,
              approvals_used: Optional[List[Dict[str, Any]]] = None,
              benchmark_scores: Optional[Dict[str, Any]] = None,
              plasticity_changes: Optional[Dict[str, Any]] = None,
              emergency_stop_used: bool = False,
              failure_streak: int = 0,
              notes: Optional[List[str]] = None) -> ReviewRecord:
        status = status or {}
        incidents = incidents or []
        violations = policy_violations or []
        approvals = approvals_used or []
        plasticity = plasticity_changes or {}

        criticals = [i for i in incidents if i.get("severity") == "critical"]
        unexplained = [i for i in criticals
                       if not i.get("resolved")
                       and i.get("type") not in ("emergency_stop",)]
        health_level = ((status.get("health") or {}).get("level")
                        or "unknown")

        recommendation, reasons = self._recommend(
            emergency_stop_used=emergency_stop_used,
            unexplained_failures=len(unexplained),
            violation_count=len(violations),
            incident_count=len(incidents),
            health_level=health_level,
            failure_streak=failure_streak)

        rollback_recommendations: List[str] = []
        if plasticity.get("applied_count", 0) and health_level == "critical":
            rollback_recommendations.append(
                "health ended critical with applied mutations: consider "
                "engine.rollback_last() and re-running without plasticity")
        if plasticity.get("rejected_count", 0) >= 3:
            rollback_recommendations.append(
                "the policy repeatedly proposed unsafe steps: review the "
                "plasticity policy deltas against SAFE_BOUNDS")

        summary = {
            "run_mode": (status.get("manifest") or {}).get("mode", "unknown"),
            "health_level": health_level,
            "incident_count": len(incidents),
            "critical_incidents": len(criticals),
            "unexplained_failures": len(unexplained),
            "policy_violations": len(violations),
            "approvals_used": [a.get("requested_permission",
                                     a.get("permission", "?"))
                               for a in approvals],
            "benchmark_scores": benchmark_scores,
            "plasticity_applied": plasticity.get("applied_count", 0),
            "plasticity_rejected": plasticity.get("rejected_count", 0),
            "plasticity_rollbacks": plasticity.get("rollback_count", 0),
            "rollback_recommendations": rollback_recommendations,
            "emergency_stop_used": emergency_stop_used,
        }
        return ReviewRecord(
            run_id=self.run_id, reviewer=self.reviewer,
            recommendation=recommendation,
            recommendation_reasons=reasons,
            summary=summary, notes=list(notes or []))

    @staticmethod
    def _recommend(emergency_stop_used: bool, unexplained_failures: int,
                   violation_count: int, incident_count: int,
                   health_level: str, failure_streak: int,
                   ) -> "tuple[str, List[str]]":
        R = NextRunRecommendation
        reasons: List[str] = []
        if failure_streak >= 3:
            reasons.append(f"{failure_streak} consecutive failed runs: "
                           "this line of work needs a rethink, not a re-run")
            return R.STOP_LINE_OF_WORK, reasons
        if emergency_stop_used or unexplained_failures > 0 \
                or health_level == "critical":
            if emergency_stop_used:
                reasons.append("an emergency stop was used; understand why "
                               "before running again")
            if unexplained_failures:
                reasons.append(f"{unexplained_failures} unexplained critical "
                               "incident(s)")
            if health_level == "critical":
                reasons.append("the run ended in critical health")
            return R.INVESTIGATE_FAILURE, reasons
        if violation_count > 0:
            reasons.append(f"{violation_count} policy violation(s): narrow "
                           "the configuration to what is actually permitted")
            return R.REDUCE_SCOPE, reasons
        if incident_count == 0 and health_level == "ok":
            reasons.append("clean run with healthy metrics: a longer "
                           "duration is justified")
            return R.EXTEND_DURATION, reasons
        reasons.append("minor warnings only: repeat at the same scope to "
                       "confirm stability")
        return R.REPEAT, reasons
