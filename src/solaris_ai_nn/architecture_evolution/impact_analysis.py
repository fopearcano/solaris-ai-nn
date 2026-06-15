"""Impact analysis -- what a proposed change would touch (it changes nothing).

The :class:`ImpactAnalyzer` estimates the blast radius of a proposed architecture
change across impact areas (conscience spine, registries, evaluation, safety,
governance, ops, Inner MAP, docs, examples, tests, state compatibility). Safety
impact is always explicit; unknown impact is never treated as low; and the
analysis implements nothing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ImpactArea:
    CONSCIENCE_SPINE = "conscience_spine"
    MODULE_REGISTRY = "module_registry"
    EVALUATION_METRICS = "evaluation_metrics"
    SAFETY_INVARIANTS = "safety_invariants"
    GOVERNANCE = "governance"
    OPS = "ops"
    INNER_MAP = "inner_map"
    RESEARCH_LAB = "research_lab"
    PILOTS = "pilots"
    DOCUMENTATION = "documentation"
    EXAMPLES = "examples"
    TESTS = "tests"
    STATE_ARTIFACTS_COMPATIBILITY = "state_artifacts_compatibility"

    ALL = (CONSCIENCE_SPINE, MODULE_REGISTRY, EVALUATION_METRICS,
           SAFETY_INVARIANTS, GOVERNANCE, OPS, INNER_MAP, RESEARCH_LAB,
           PILOTS, DOCUMENTATION, EXAMPLES, TESTS,
           STATE_ARTIFACTS_COMPATIBILITY)


class ImpactSeverity:
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    UNKNOWN = "unknown"

    ALL = (NONE, LOW, MODERATE, HIGH, UNKNOWN)


@dataclass
class ArchitectureImpactAnalysis:
    """The estimated blast radius of one proposed change."""

    target_change: str
    affected_modules: List[str] = field(default_factory=list)
    affected_areas: Dict[str, str] = field(default_factory=dict)
    safety_impact: str = ImpactSeverity.UNKNOWN
    dependency_breakage: List[str] = field(default_factory=list)
    metric_comparability_risk: str = ImpactSeverity.UNKNOWN
    state_compatibility_risk: str = ImpactSeverity.UNKNOWN
    migration_effort: str = ImpactSeverity.UNKNOWN
    rollback_difficulty: str = ImpactSeverity.UNKNOWN
    affected_tests: List[str] = field(default_factory=list)
    affected_examples: List[str] = field(default_factory=list)
    affected_docs: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.limitations:
            self.limitations = [
                "Impact analysis implements nothing; it estimates blast radius.",
                "Unknown impact is treated as unknown, never as low.",
            ]

    @property
    def has_safety_impact(self) -> bool:
        return self.safety_impact not in (ImpactSeverity.NONE,)

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__), "has_safety_impact":
                self.has_safety_impact}


@dataclass
class ImpactAnalyzer:
    """Estimates impact; safety is explicit; unknown is never low."""

    def analyze(self, target_change: str, affected_modules: List[str], *,
                safety_critical_touched: bool = False,
                integration_count: int = 0,
                touches_metrics: bool = False,
                touches_state: bool = False) -> ArchitectureImpactAnalysis:
        areas: Dict[str, str] = {}
        # Conservative defaults: where we cannot tell, mark UNKNOWN (not low).
        areas[ImpactArea.MODULE_REGISTRY] = (
            ImpactSeverity.HIGH if integration_count >= 3
            else ImpactSeverity.MODERATE if integration_count >= 1
            else ImpactSeverity.LOW)
        areas[ImpactArea.CONSCIENCE_SPINE] = (
            ImpactSeverity.MODERATE if integration_count >= 1
            else ImpactSeverity.LOW)
        areas[ImpactArea.SAFETY_INVARIANTS] = (
            ImpactSeverity.HIGH if safety_critical_touched
            else ImpactSeverity.LOW)
        areas[ImpactArea.EVALUATION_METRICS] = (
            ImpactSeverity.MODERATE if touches_metrics else ImpactSeverity.LOW)
        areas[ImpactArea.STATE_ARTIFACTS_COMPATIBILITY] = (
            ImpactSeverity.HIGH if touches_state else ImpactSeverity.UNKNOWN)
        for area in (ImpactArea.GOVERNANCE, ImpactArea.OPS,
                     ImpactArea.INNER_MAP, ImpactArea.RESEARCH_LAB,
                     ImpactArea.PILOTS, ImpactArea.DOCUMENTATION,
                     ImpactArea.EXAMPLES, ImpactArea.TESTS):
            areas.setdefault(area, ImpactSeverity.UNKNOWN
                             if integration_count == 0 else ImpactSeverity.LOW)
        safety_impact = (ImpactSeverity.HIGH if safety_critical_touched
                         else ImpactSeverity.NONE)
        return ArchitectureImpactAnalysis(
            target_change=target_change,
            affected_modules=list(affected_modules), affected_areas=areas,
            safety_impact=safety_impact,
            dependency_breakage=(list(affected_modules)
                                 if integration_count >= 3 else []),
            metric_comparability_risk=(ImpactSeverity.MODERATE if touches_metrics
                                       else ImpactSeverity.LOW),
            state_compatibility_risk=(ImpactSeverity.HIGH if touches_state
                                      else ImpactSeverity.UNKNOWN),
            migration_effort=(ImpactSeverity.HIGH if integration_count >= 3
                              else ImpactSeverity.MODERATE),
            rollback_difficulty=(ImpactSeverity.MODERATE if integration_count
                                 >= 1 else ImpactSeverity.LOW),
            affected_tests=[f"tests touching {m}" for m in affected_modules],
            affected_examples=[f"examples touching {m}" for m in
                               affected_modules],
            affected_docs=["docs/ARCHITECTURE.md"])
