"""Pilot-2 decision gate -- what should happen next after read-only exposure.

The :class:`Pilot2DecisionGate` weighs grounding evidence, source reliability,
safety incidents, the command boundary, comparison analyzability, and resource
budget into a recommendation. Actuation is never an enabled action; a Pilot-3
limited-embodiment recommendation, if made, is *planning-only*.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class Pilot2DecisionOption:
    REPEAT_PILOT2_WITH_FIXTURES = "repeat_pilot2_with_fixtures"
    REPEAT_PILOT2_WITH_CURATED_SOURCES = "repeat_pilot2_with_curated_sources"
    EXTEND_READ_ONLY_SOAK = "extend_read_only_soak"
    REDUCE_SOURCE_COMPLEXITY = "reduce_source_complexity"
    INCREASE_SOURCE_VARIETY = "increase_source_variety"
    RETURN_TO_NURSERY_ONLY = "return_to_nursery_only"
    REVISE_SENSORY_MEMBRANE = "revise_sensory_membrane"
    PREPARE_PILOT3_LIMITED_EMBODIMENT = "prepare_pilot3_limited_embodiment"
    ARCHIVE_AND_STOP = "archive_and_stop"

    ALL = (REPEAT_PILOT2_WITH_FIXTURES, REPEAT_PILOT2_WITH_CURATED_SOURCES,
           EXTEND_READ_ONLY_SOAK, REDUCE_SOURCE_COMPLEXITY,
           INCREASE_SOURCE_VARIETY, RETURN_TO_NURSERY_ONLY,
           REVISE_SENSORY_MEMBRANE, PREPARE_PILOT3_LIMITED_EMBODIMENT,
           ARCHIVE_AND_STOP)


@dataclass
class Pilot2DecisionResult:
    recommendation: str
    rationale: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    required_actions: List[str] = field(default_factory=list)
    optional_actions: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    confidence: float = 0.0
    planning_only: bool = False
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class Pilot2DecisionGate:
    """Decides the Pilot-2 next step (never enabling actuation)."""

    def decide(self, *, grounding: Any = None, reliability: Any = None,
               safety_incident_count: int = 0,
               command_confusion_count: int = 0,
               comparison_analyzable: bool = True,
               resource_over_budget: bool = False,
               unsafe_source_count: int = 0) -> Pilot2DecisionResult:
        blockers: List[str] = []
        rationale: List[str] = []
        required: List[str] = []
        optional: List[str] = []

        has_grounding = bool(getattr(grounding, "has_grounding_evidence",
                                     False))
        best_quality = getattr(grounding, "best_quality", "unsupported")
        if reliability is not None:
            unsafe = getattr(reliability, "unsafe_sources", lambda: [])()
            unsafe_source_count = max(unsafe_source_count, len(unsafe))

        # -- blockers --
        if safety_incident_count > 0:
            blockers.append("unresolved critical safety incident")
        if command_confusion_count > 0:
            blockers.append("sensory input attempted to become a command")
        if unsafe_source_count > 0:
            blockers.append(f"{unsafe_source_count} unsafe source(s) active")
        if not comparison_analyzable:
            blockers.append("comparison is not analyzable")
        if resource_over_budget:
            blockers.append("resource budget exceeded")

        recommendation, conf, planning_only = self._choose(
            blockers, has_grounding, best_quality, unsafe_source_count,
            rationale, required, optional)

        evidence_refs = [getattr(e, "evidence_id", "")
                         for e in getattr(grounding, "evidence", [])][:8]
        return Pilot2DecisionResult(
            recommendation=recommendation, rationale=rationale,
            blockers=blockers, required_actions=required,
            optional_actions=optional, confidence=conf,
            planning_only=planning_only,
            evidence_refs=evidence_refs,
            limitations=[
                "Pilot-2 is read-only; actuation is never an enabled action.",
                "Differences are observed associations, not proven causes.",
                "No consciousness/understanding is claimed.",
            ])

    def _choose(self, blockers: List[str], has_grounding: bool,
                best_quality: str, unsafe_source_count: int,
                rationale: List[str], required: List[str],
                optional: List[str]) -> "tuple[str, float, bool]":
        D = Pilot2DecisionOption
        if unsafe_source_count > 0:
            rationale.append("an unsafe source is active; disable it first")
            required.append("disable unsafe source(s) and re-run preflight")
            return D.REVISE_SENSORY_MEMBRANE, 0.6, False
        if blockers:
            rationale.append("blockers prevent advancing")
            if any("command" in b for b in blockers):
                required.append("audit the source/command boundary")
                return D.REVISE_SENSORY_MEMBRANE, 0.6, False
            if any("safety" in b for b in blockers):
                required.append("resolve safety incidents")
            if any("analyzable" in b for b in blockers):
                required.append("ensure full provenance and comparable arms")
                return D.REPEAT_PILOT2_WITH_FIXTURES, 0.5, False
            if any("budget" in b for b in blockers):
                return D.REDUCE_SOURCE_COMPLEXITY, 0.5, False
            return D.REPEAT_PILOT2_WITH_FIXTURES, 0.5, False

        if best_quality == "strong":
            rationale.append("strong grounding and a clean run")
            optional.append("a future Pilot-3 limited embodiment could be "
                            "*planned* (planning only; no actuation)")
            return D.EXTEND_READ_ONLY_SOAK, 0.7, False
        if best_quality == "moderate":
            rationale.append("moderate grounding; extend cautiously")
            return D.EXTEND_READ_ONLY_SOAK, 0.6, False
        if has_grounding:
            rationale.append("weak grounding; repeat with curated sources")
            optional.append("increase source variety next run")
            return D.REPEAT_PILOT2_WITH_CURATED_SOURCES, 0.55, False
        rationale.append("no grounding evidence; repeat with fixtures or "
                         "return to nursery-only")
        optional.append("increase_source_variety")
        return D.REPEAT_PILOT2_WITH_FIXTURES, 0.5, False
