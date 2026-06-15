"""Module lifecycle classification -- a recommendation, never a deletion.

The :class:`ModuleLifecycleClassifier` turns research/ablation/safety evidence
into a *recommended* lifecycle class for a module (core_keep, candidate_for_
pruning, needs_revision, insufficient_evidence, ...). Safety-critical modules can
never be classified as a pruning candidate on performance evidence alone; missing
evidence yields ``insufficient_evidence``, never pruning; and every assessment is
a recommendation only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ModuleLifecycleClass:
    CORE_KEEP = "core_keep"
    PROMOTE_TO_CORE = "promote_to_core"
    EXPERIMENTAL_KEEP = "experimental_keep"
    NEEDS_REVISION = "needs_revision"
    CANDIDATE_FOR_PRUNING = "candidate_for_pruning"
    CANDIDATE_FOR_QUARANTINE = "candidate_for_quarantine"
    DEPRECATED_KEEP_FOR_COMPATIBILITY = "deprecated_keep_for_compatibility"
    SAFETY_CRITICAL_DO_NOT_PRUNE = "safety_critical_do_not_prune"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    UNKNOWN = "unknown"

    ALL = (CORE_KEEP, PROMOTE_TO_CORE, EXPERIMENTAL_KEEP, NEEDS_REVISION,
           CANDIDATE_FOR_PRUNING, CANDIDATE_FOR_QUARANTINE,
           DEPRECATED_KEEP_FOR_COMPATIBILITY, SAFETY_CRITICAL_DO_NOT_PRUNE,
           INSUFFICIENT_EVIDENCE, UNKNOWN)
    # Classes that recommend removal/quarantine (never applied to safety modules).
    REMOVAL_LEANING = frozenset({CANDIDATE_FOR_PRUNING,
                                 CANDIDATE_FOR_QUARANTINE})


@dataclass
class ModuleLifecycleAssessment:
    """One module's recommended lifecycle class with rationale and evidence."""

    module_name: str
    lifecycle_class: str = ModuleLifecycleClass.UNKNOWN
    safety_critical: bool = False
    rationale: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    confidence: str = "low"
    recommendation_only: bool = True
    limitations: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.limitations:
            self.limitations = [
                "Lifecycle class is a recommendation, not an applied change.",
                "A module can be harmful in one profile and useful in another.",
                "Missing evidence yields insufficient_evidence, not pruning.",
            ]

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ModuleLifecycleClassifier:
    """Classifies a module's recommended lifecycle from evidence."""

    def classify(self, module_name: str, *, safety_critical: bool = False,
                 effect_value: Optional[str] = None,
                 integration_count: int = 0, failure_rate: float = 0.0,
                 overhead_cost: float = 0.0,
                 evidence_refs: Optional[List[str]] = None,
                 has_evidence: bool = True) -> ModuleLifecycleAssessment:
        evidence_refs = list(evidence_refs or [])
        rationale: List[str] = []
        L = ModuleLifecycleClass

        # Safety-critical modules are never pruned on performance evidence.
        if safety_critical:
            rationale.append("safety-critical: protected from pruning by "
                             "performance evidence alone")
            return ModuleLifecycleAssessment(
                module_name=module_name,
                lifecycle_class=L.SAFETY_CRITICAL_DO_NOT_PRUNE,
                safety_critical=True, rationale=rationale,
                evidence_refs=evidence_refs,
                confidence="high" if evidence_refs else "moderate")

        # Missing evidence -> insufficient_evidence (never pruning).
        if not has_evidence or effect_value is None or not evidence_refs:
            rationale.append("insufficient evidence to recommend a change")
            return ModuleLifecycleAssessment(
                module_name=module_name,
                lifecycle_class=L.INSUFFICIENT_EVIDENCE,
                rationale=rationale, evidence_refs=evidence_refs,
                confidence="inconclusive")

        confidence = "moderate" if integration_count >= 3 else "low"
        ev = str(effect_value)
        if ev == "strong_positive":
            klass = (L.PROMOTE_TO_CORE if integration_count >= 3
                     else L.CORE_KEEP)
            rationale.append("repeated positive evidence")
        elif ev == "weak_positive":
            klass = L.CORE_KEEP if integration_count >= 2 else L.EXPERIMENTAL_KEEP
            rationale.append("positive but modest evidence")
        elif ev == "neutral":
            klass = (L.NEEDS_REVISION if overhead_cost > 0.5
                     else L.EXPERIMENTAL_KEEP)
            rationale.append("no observed benefit; review overhead")
        elif ev == "mixed":
            klass = L.NEEDS_REVISION
            rationale.append("mixed effect across metrics/profiles")
        elif ev in ("negative", "harmful"):
            # High failure or high overhead -> quarantine before pruning.
            if failure_rate >= 0.5 or overhead_cost >= 0.7:
                klass = L.CANDIDATE_FOR_QUARANTINE
                rationale.append("negative evidence with high failure/overhead;"
                                 " quarantine before any pruning")
            else:
                klass = L.CANDIDATE_FOR_PRUNING
                rationale.append("removing the module did not worsen (and may "
                                 "have improved) metrics in this profile")
        else:
            klass = L.INSUFFICIENT_EVIDENCE
            rationale.append("unrecognized effect value")
        return ModuleLifecycleAssessment(
            module_name=module_name, lifecycle_class=klass,
            rationale=rationale, evidence_refs=evidence_refs,
            confidence=confidence)

    def classify_inventory(self, inventory: Any, effects: Dict[str, str],
                           evidence_by_module: Optional[Dict[str, List[str]]]
                           = None) -> Dict[str, ModuleLifecycleAssessment]:
        evidence_by_module = evidence_by_module or {}
        out: Dict[str, ModuleLifecycleAssessment] = {}
        for name, entry in getattr(inventory, "entries", {}).items():
            if not entry.available:
                out[name] = ModuleLifecycleAssessment(
                    module_name=name,
                    lifecycle_class=ModuleLifecycleClass.INSUFFICIENT_EVIDENCE,
                    rationale=["module unavailable"], confidence="inconclusive")
                continue
            out[name] = self.classify(
                name, safety_critical=entry.safety_critical,
                effect_value=effects.get(name),
                evidence_refs=evidence_by_module.get(
                    name, entry.research_evidence_refs),
                has_evidence=name in effects)
        return out

    @staticmethod
    def summary(assessments: Dict[str, ModuleLifecycleAssessment],
                ) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for a in assessments.values():
            counts[a.lifecycle_class] = counts.get(a.lifecycle_class, 0) + 1
        return counts
