"""Next-action recommender -- the safest useful thing to do next.

:class:`NextActionRecommender` reads the current evidence (safety status,
assurance status, pilot gates, research findings, architecture roadmap, ops
incidents, design debt, missing artifacts) and recommends the next safe action.
Safety review always comes first when a critical blocker exists; when no evidence
exists it recommends a baseline/research run; when architecture evidence exists it
recommends an architecture review. It never recommends real-world actuation and
never recommends disabling safety.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class NextActionPriority:
    IMMEDIATE = "immediate"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    ORDER = {IMMEDIATE: 0, HIGH: 1, MEDIUM: 2, LOW: 3}


class NextActionType:
    RUN_SAFETY_FAST_CHECK = "run_safety_fast_check"
    RUN_SAFETY_FULL_CHECK = "run_safety_full_check"
    RUN_RED_TEAM_SUITE = "run_red_team_suite"
    GENERATE_ASSURANCE_CASE = "generate_assurance_case"
    RUN_RESEARCH_BASELINE = "run_research_baseline"
    RUN_ARCHITECTURE_REVIEW = "run_architecture_review"
    GENERATE_POST_PILOT_ANALYSIS = "generate_post_pilot_analysis"
    GENERATE_PILOT_PLAN = "generate_pilot_plan"
    INSPECT_MISSING_ARTIFACTS = "inspect_missing_artifacts"
    REVIEW_ADR = "review_ADR"
    STOP_AND_REVIEW = "stop_and_review"
    ARCHIVE_AND_STOP = "archive_and_stop"

    ALL = (RUN_SAFETY_FAST_CHECK, RUN_SAFETY_FULL_CHECK, RUN_RED_TEAM_SUITE,
           GENERATE_ASSURANCE_CASE, RUN_RESEARCH_BASELINE,
           RUN_ARCHITECTURE_REVIEW, GENERATE_POST_PILOT_ANALYSIS,
           GENERATE_PILOT_PLAN, INSPECT_MISSING_ARTIFACTS, REVIEW_ADR,
           STOP_AND_REVIEW, ARCHIVE_AND_STOP)


@dataclass
class NextActionRecommendation:
    action_type: str
    priority: str
    rationale: str
    evidence_refs: List[str] = field(default_factory=list)
    profile_hint: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class NextActionRecommender:
    """Recommends the next safe action from current evidence."""

    def recommend(self, *,
                  safety_status: Optional[Dict[str, Any]] = None,
                  assurance_status: Optional[Dict[str, Any]] = None,
                  pilot_gates: Optional[Dict[str, Any]] = None,
                  research_findings: Optional[Dict[str, Any]] = None,
                  architecture_roadmap: Optional[Dict[str, Any]] = None,
                  ops_incidents: Optional[List[Dict[str, Any]]] = None,
                  design_debt: Optional[Dict[str, Any]] = None,
                  missing_artifacts: Optional[List[str]] = None,
                  ) -> List[NextActionRecommendation]:
        recs: List[NextActionRecommendation] = []

        # 1. Safety first: a critical blocker or missing safety state wins.
        if safety_status is None:
            recs.append(NextActionRecommendation(
                NextActionType.RUN_SAFETY_FAST_CHECK,
                NextActionPriority.IMMEDIATE,
                "no recent safety-invariant state; establish it before any run",
                profile_hint="safety_fast_check"))
        elif self._critical(safety_status):
            recs.append(NextActionRecommendation(
                NextActionType.RUN_SAFETY_FULL_CHECK,
                NextActionPriority.IMMEDIATE,
                "a critical safety blocker exists; run the full safety review "
                "and triage before anything else",
                evidence_refs=["safety_status"],
                profile_hint="safety_full_check"))
            recs.append(NextActionRecommendation(
                NextActionType.STOP_AND_REVIEW, NextActionPriority.IMMEDIATE,
                "do not launch any profile while a critical safety blocker is "
                "open"))

        # 2. No evidence yet: recommend a baseline / research run.
        if not research_findings:
            recs.append(NextActionRecommendation(
                NextActionType.RUN_RESEARCH_BASELINE,
                NextActionPriority.HIGH,
                "no research evidence exists yet; run a baseline so later "
                "claims can be compared against a trivial reference",
                profile_hint="research_baseline_random"))
        else:
            # 3. Research evidence exists: recommend an architecture review.
            recs.append(NextActionRecommendation(
                NextActionType.RUN_ARCHITECTURE_REVIEW,
                NextActionPriority.HIGH,
                "research evidence exists; compile an architecture review to "
                "decide what to keep, revise, or (recommend) pruning",
                evidence_refs=["research_findings"],
                profile_hint="architecture_review"))

        # 4. Assurance case missing while safety is otherwise fine.
        if safety_status is not None and not self._critical(safety_status) \
                and not assurance_status:
            recs.append(NextActionRecommendation(
                NextActionType.GENERATE_ASSURANCE_CASE,
                NextActionPriority.MEDIUM,
                "safety checks exist but no assurance case has been compiled",
                profile_hint="assurance_case_compile"))

        # 5. Open ADRs / critical design debt.
        if design_debt and int(design_debt.get("critical_count", 0) or 0) > 0:
            recs.append(NextActionRecommendation(
                NextActionType.REVIEW_ADR, NextActionPriority.MEDIUM,
                f"{design_debt['critical_count']} critical design-debt item(s) "
                "await an ADR review", evidence_refs=["design_debt"]))

        # 6. Missing artifacts.
        if missing_artifacts:
            recs.append(NextActionRecommendation(
                NextActionType.INSPECT_MISSING_ARTIFACTS,
                NextActionPriority.LOW,
                f"{len(missing_artifacts)} expected artifact(s) are missing",
                evidence_refs=list(missing_artifacts)[:10]))

        recs.sort(key=lambda r: NextActionPriority.ORDER.get(r.priority, 9))
        return recs

    @staticmethod
    def _critical(safety_status: Dict[str, Any]) -> bool:
        return bool(
            safety_status.get("critical_failure")
            or safety_status.get("critical")
            or str(safety_status.get("status", "")).lower() == "critical"
            or int(safety_status.get("unresolved_blocker_count", 0) or 0) > 0)

    def top(self, **kwargs) -> Optional[NextActionRecommendation]:
        recs = self.recommend(**kwargs)
        return recs[0] if recs else None
