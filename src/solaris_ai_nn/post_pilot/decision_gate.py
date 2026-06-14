"""Post-pilot Phase-2 decision gate -- what should happen next, and why.

The :class:`Phase2DecisionGate` weighs exit criteria, growth classification,
regression signals, trace-audit quality, safety/governance incidents, resource
budget, reproducibility completeness, and report completeness into a single
recommendation with rationale, blockers, and required/optional actions.
``ready_for_pilot2`` is only reachable when the strict readiness conditions
all hold.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .accumulation_vs_growth import GrowthClassification
from .regression_analysis import RegressionSeverity


class DecisionOption:
    REPEAT_PILOT1 = "repeat_pilot1"
    EXTEND_TO_60_DAYS = "extend_to_60_days"
    EXTEND_TO_90_DAYS = "extend_to_90_days"
    REVISE_ARCHITECTURE = "revise_architecture"
    REDUCE_COMPLEXITY = "reduce_complexity"
    INCREASE_ECOLOGY_VARIETY = "increase_ecology_variety"
    INCREASE_CONSOLIDATION = "increase_consolidation"
    DISABLE_UNHELPFUL_MODULE = "disable_unhelpful_module"
    RUN_REGRESSION_DIAGNOSTICS = "run_regression_diagnostics"
    ARCHIVE_AND_STOP = "archive_and_stop"
    READY_FOR_PILOT2 = "ready_for_pilot2"

    ALL = (REPEAT_PILOT1, EXTEND_TO_60_DAYS, EXTEND_TO_90_DAYS,
           REVISE_ARCHITECTURE, REDUCE_COMPLEXITY, INCREASE_ECOLOGY_VARIETY,
           INCREASE_CONSOLIDATION, DISABLE_UNHELPFUL_MODULE,
           RUN_REGRESSION_DIAGNOSTICS, ARCHIVE_AND_STOP, READY_FOR_PILOT2)


@dataclass
class DecisionGateResult:
    """The Phase-2 recommendation and the reasoning behind it."""

    recommendation: str
    rationale: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    required_actions: List[str] = field(default_factory=list)
    optional_actions: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    confidence: float = 0.0
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class Phase2DecisionGate:
    """Decides the Phase-2 next step from the post-pilot analysis inputs."""

    uptime_threshold: float = 0.9

    def decide(self, *, exit_decision: Any = None, growth: Any = None,
               regression: Any = None, trace_audit: Any = None,
               artifacts: Any = None,
               safety_incident_count: int = 0,
               resource_over_budget: bool = False,
               reproducibility_complete: bool = True,
               report_complete: bool = True,
               identity_continuity_failed: bool = False,
               ) -> DecisionGateResult:
        blockers: List[str] = []
        rationale: List[str] = []
        required: List[str] = []
        optional: List[str] = []

        growth_class = getattr(growth, "final_classification",
                               GrowthClassification.INCONCLUSIVE)
        reg_severity = getattr(regression, "overall_severity",
                               RegressionSeverity.NONE)
        traceability = getattr(trace_audit, "traceability_score", 0.0)
        analyzable = traceability >= 0.5
        exit_ok = getattr(exit_decision, "success", False) \
            if exit_decision is not None else False
        uptime = self._uptime(artifacts)

        # -- blockers (prevent readiness) --
        if safety_incident_count > 0:
            blockers.append("unresolved critical safety incidents present")
        if not analyzable:
            blockers.append("artifacts are not analyzable enough "
                            f"(traceability {traceability})")
        if uptime is not None and uptime < self.uptime_threshold:
            blockers.append(f"uptime/checkpoint reliability below threshold "
                            f"({uptime})")
        if resource_over_budget:
            blockers.append("resource budget exceeded and unmanaged")
        if identity_continuity_failed:
            blockers.append("unresolved identity continuity failure")

        # -- choose the recommendation --
        recommendation, conf = self._choose(
            growth_class, reg_severity, blockers, exit_ok, analyzable,
            rationale, required, optional, reproducibility_complete,
            report_complete)

        evidence_refs = []
        if artifacts is not None:
            evidence_refs = list(getattr(getattr(artifacts, "index", None),
                                         "present", []) or [])
        return DecisionGateResult(
            recommendation=recommendation, rationale=rationale,
            blockers=blockers, required_actions=required,
            optional_actions=optional, evidence_refs=evidence_refs,
            confidence=conf,
            limitations=[
                "This gate evaluates operational and developmental-evidence "
                "proxies only; it makes no claim about consciousness.",
                "Recommendations are conservative when evidence is missing.",
            ])

    def _choose(self, growth_class: str, reg_severity: str,
                blockers: List[str], exit_ok: bool, analyzable: bool,
                rationale: List[str], required: List[str],
                optional: List[str], reproducibility_complete: bool,
                report_complete: bool) -> "tuple[str, float]":
        D = DecisionOption
        # Severe regression overrides everything else.
        if reg_severity in (RegressionSeverity.CRITICAL,):
            rationale.append("critical regression detected")
            required.append("perform an architecture review before any rerun")
            return D.REVISE_ARCHITECTURE, 0.7
        if reg_severity == RegressionSeverity.HIGH:
            rationale.append("high-severity regression detected")
            required.append("run regression diagnostics")
            return D.RUN_REGRESSION_DIAGNOSTICS, 0.6
        if growth_class == GrowthClassification.REGRESSION:
            rationale.append("analysis classified the run as regression")
            return D.REVISE_ARCHITECTURE, 0.6

        if not report_complete:
            required.append("complete the pilot report")
        if not reproducibility_complete:
            required.append("complete the reproducibility package")

        # Readiness for Pilot-2 requires no blockers AND real evidence.
        ready = (not blockers and analyzable and exit_ok
                 and growth_class in (GrowthClassification.WEAK_GROWTH,
                                      GrowthClassification.MODERATE_GROWTH,
                                      GrowthClassification.STRONG_GROWTH))
        if ready:
            rationale.append("no blockers; analyzable; at least weak "
                             "structural-change evidence")
            optional.append("consider extending runtime in Pilot-2")
            conf = {GrowthClassification.STRONG_GROWTH: 0.8,
                    GrowthClassification.MODERATE_GROWTH: 0.7,
                    GrowthClassification.WEAK_GROWTH: 0.55}[growth_class]
            return D.READY_FOR_PILOT2, conf

        if blockers:
            rationale.append("blockers prevent advancing to Pilot-2")
            if any("safety" in b for b in blockers):
                required.append("resolve safety incidents")
            if any("identity" in b for b in blockers):
                return D.REVISE_ARCHITECTURE, 0.6
            return D.REPEAT_PILOT1, 0.5

        if growth_class == GrowthClassification.MOSTLY_ACCUMULATION:
            rationale.append("mostly accumulation, not structural growth")
            optional += ["increase_ecology_variety", "increase_consolidation"]
            return D.INCREASE_ECOLOGY_VARIETY, 0.5
        if growth_class == GrowthClassification.INCONCLUSIVE:
            rationale.append("evidence inconclusive; repeat with better "
                             "observability")
            required.append("ensure full artifact capture next run")
            return D.REPEAT_PILOT1, 0.5
        if growth_class == GrowthClassification.STRONG_GROWTH:
            rationale.append("strong growth and clean run; extend runtime")
            return D.EXTEND_TO_60_DAYS, 0.65
        rationale.append("some growth; repeat or extend cautiously")
        return D.REPEAT_PILOT1, 0.5

    @staticmethod
    def _uptime(artifacts: Any) -> Optional[float]:
        data = getattr(artifacts, "data", {}) if artifacts is not None else {}
        report = (data or {}).get("pilot_report") or {}
        sections = report.get("sections") or {}
        if "uptime_ratio" in sections:
            try:
                return float(sections["uptime_ratio"])
            except (TypeError, ValueError):
                return None
        return None
