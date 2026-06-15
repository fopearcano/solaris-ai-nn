"""Study design -- a bounded, comparative sensorium differentiation study.

A :class:`SensoriumStudyDesign` pins the research question, the arms (each a
:class:`SensoriumStudyArm` with a sensorium condition), the bounds, and the
metrics. Every study is bounded; live read-only arms require governance approval;
missing live data yields an *inconclusive* arm, not a failure; and no study may
enable real-world actuation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class SensoriumStudyCondition:
    HUMAN_LIKE_ONLY = "human_like_only"
    NON_HUMAN_ONLY = "non_human_only"
    MACHINE_NATIVE_ONLY = "machine_native_only"
    ABSENCE_HEAVY = "absence_heavy"
    MIXED_PLURAL_SENSORIUM = "mixed_plural_sensorium"
    HUMAN_LABELLED = "human_labelled"
    FEATURE_ONLY = "feature_only"
    PASSIVE_PARSER = "passive_parser"
    ADAPTIVE_RECEPTORS = "adaptive_receptors"
    FIXED_ATTENTION = "fixed_attention"
    ADAPTIVE_ATTENTION = "adaptive_attention"
    FIXTURE_REPLAY = "fixture_replay"
    LIVE_READ_ONLY = "live_read_only"

    ALL = (HUMAN_LIKE_ONLY, NON_HUMAN_ONLY, MACHINE_NATIVE_ONLY, ABSENCE_HEAVY,
           MIXED_PLURAL_SENSORIUM, HUMAN_LABELLED, FEATURE_ONLY, PASSIVE_PARSER,
           ADAPTIVE_RECEPTORS, FIXED_ATTENTION, ADAPTIVE_ATTENTION,
           FIXTURE_REPLAY, LIVE_READ_ONLY)
    # Conditions that read a real, outside-world source (need governance).
    LIVE = frozenset({LIVE_READ_ONLY})


@dataclass
class SensoriumStudyArm:
    """One arm of a study: a labelled condition with a sensorium profile type."""

    arm_id: str
    condition: str
    profile_type: str
    title: str = ""
    live: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.condition not in SensoriumStudyCondition.ALL:
            raise ValueError(f"unknown study condition {self.condition!r}")
        if self.condition in SensoriumStudyCondition.LIVE:
            self.live = True

    @property
    def requires_governance(self) -> bool:
        return self.live

    def to_dict(self) -> Dict[str, Any]:
        return {
            "arm_id": self.arm_id,
            "condition": self.condition,
            "profile_type": self.profile_type,
            "title": self.title,
            "live": self.live,
            "requires_governance": self.requires_governance,
            "metadata": dict(self.metadata),
        }


@dataclass
class SensoriumStudyResult:
    """The serialisable outcome of one study arm."""

    arm_id: str
    condition: str
    blocked: bool = False
    inconclusive: bool = False
    reasons: List[str] = field(default_factory=list)
    world_signature: Optional[Dict[str, Any]] = None
    structure_metrics: Optional[Dict[str, Any]] = None
    modality_fingerprints: List[Dict[str, Any]] = field(default_factory=list)
    ontology_drift: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SensoriumStudyDesign:
    """A bounded comparative sensorium study."""

    study_id: str = field(
        default_factory=lambda: f"SSD_{int(time.time())}")
    title: str = "Sensorium differentiation study"
    research_question: str = ("What kind of intelligence-like internal "
                              "structure emerges from different forms of "
                              "perception?")
    arms: List[SensoriumStudyArm] = field(default_factory=list)
    data_source_refs: List[str] = field(default_factory=list)
    modality_configuration: Dict[str, Any] = field(default_factory=dict)
    ticks: int = 80
    max_events: int = 600
    seed: int = 7
    live_governance_required: bool = True
    metrics: List[str] = field(default_factory=list)
    expected_artifacts: List[str] = field(
        default_factory=lambda: ["SENSORIUM_DIFFERENTIATION_REPORT.json"])
    limitations: List[str] = field(default_factory=lambda: [
        "Bounded fixtures are a rehearsal, not real-world generalisation.",
        "World signatures are observable structure, not subjective experience.",
        "Human labels are annotations, never ground truth.",
    ])
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_arm(self, arm: SensoriumStudyArm) -> None:
        self.arms.append(arm)

    @property
    def has_live_arm(self) -> bool:
        return any(a.live for a in self.arms)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "study_id": self.study_id,
            "title": self.title,
            "research_question": self.research_question,
            "arms": [a.to_dict() for a in self.arms],
            "data_source_refs": list(self.data_source_refs),
            "modality_configuration": dict(self.modality_configuration),
            "ticks": self.ticks,
            "max_events": self.max_events,
            "seed": self.seed,
            "live_governance_required": self.live_governance_required,
            "metrics": list(self.metrics),
            "expected_artifacts": list(self.expected_artifacts),
            "limitations": list(self.limitations),
            "metadata": dict(self.metadata),
        }


def default_study_design() -> SensoriumStudyDesign:
    """The canonical human-like vs non-human vs mixed differentiation study."""
    from .sensorium_profiles import SensoriumProfileType as P

    design = SensoriumStudyDesign(title="Human-like vs non-human vs mixed")
    arms = [
        ("human_like", SensoriumStudyCondition.HUMAN_LIKE_ONLY,
         P.HUMAN_LIKE_TEXT_LIGHT_TEMPERATURE),
        ("non_human", SensoriumStudyCondition.NON_HUMAN_ONLY,
         P.RF_ECHO_VIBRATION_MAGNETIC),
        ("machine_native", SensoriumStudyCondition.MACHINE_NATIVE_ONLY,
         P.THERMAL_PRESSURE_MACHINE_RHYTHM),
        ("absence_heavy", SensoriumStudyCondition.ABSENCE_HEAVY,
         P.ABSENCE_SILENCE_DOMINANT),
        ("mixed", SensoriumStudyCondition.MIXED_PLURAL_SENSORIUM,
         P.MIXED_HUMAN_NONHUMAN),
        ("feature_only", SensoriumStudyCondition.FEATURE_ONLY,
         P.FEATURE_ONLY_NO_LABELS),
        ("human_labelled", SensoriumStudyCondition.HUMAN_LABELLED,
         P.HUMAN_LABEL_CONTAMINATED),
        ("passive", SensoriumStudyCondition.PASSIVE_PARSER,
         P.PASSIVE_EVENT_LIST),
        ("adaptive", SensoriumStudyCondition.ADAPTIVE_RECEPTORS,
         P.ADAPTIVE_RECEPTOR_FIELD),
    ]
    for arm_id, condition, profile_type in arms:
        design.add_arm(SensoriumStudyArm(
            arm_id=arm_id, condition=condition, profile_type=profile_type,
            title=arm_id.replace("_", " ")))
    return design
