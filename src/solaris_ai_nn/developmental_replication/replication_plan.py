"""Replication plan -- which conditions to compare, by arm.

The :class:`ReplicationPlan` declares the conditions under which independent
Solaris developmental runs are compared: same/different seed, same/different
sensorium, controls, ablations, fixture/live, and falsification-style
conditions. The plan *compares existing artifacts by default*; it does not run
unbounded soaks, and live comparisons require governance. A missing arm is
marked unavailable/inconclusive rather than crashing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ReplicationCondition:
    SAME_SEED_SAME_FIXTURE = "same_seed_same_fixture"
    DIFFERENT_SEED_SAME_FIXTURE = "different_seed_same_fixture"
    SAME_ARCHITECTURE_DIFFERENT_SENSORIUM = \
        "same_architecture_different_sensorium"
    HUMAN_LIKE_ONLY = "human_like_only"
    NON_HUMAN_ONLY = "non_human_only"
    MIXED_PLURAL_SENSORIUM = "mixed_plural_sensorium"
    FEATURE_ONLY = "feature_only"
    HUMAN_LABEL_HEAVY = "human_label_heavy"
    FIXTURE_ONLY = "fixture_only"
    LIVE_READ_ONLY_IF_AVAILABLE = "live_read_only_if_available"
    PASSIVE_PARSER_CONTROL = "passive_parser_control"
    NO_METABOLISM_CONTROL = "no_metabolism_control"
    NO_ONTOGENESIS_CONTROL = "no_ontogenesis_control"
    NO_SEMIOGENESIS_CONTROL = "no_semiogenesis_control"
    NO_COGNITION_CONTROL = "no_cognition_control"
    NO_DESIRE_ACTION_CONTROL = "no_desire_action_control"
    RANDOMIZED_EVENT_ORDER = "randomized_event_order"
    SILENCE_DEPRIVATION_CONDITION = "silence_deprivation_condition"
    OVERLOAD_CONDITION = "overload_condition"

    ALL = (SAME_SEED_SAME_FIXTURE, DIFFERENT_SEED_SAME_FIXTURE,
           SAME_ARCHITECTURE_DIFFERENT_SENSORIUM, HUMAN_LIKE_ONLY,
           NON_HUMAN_ONLY, MIXED_PLURAL_SENSORIUM, FEATURE_ONLY,
           HUMAN_LABEL_HEAVY, FIXTURE_ONLY, LIVE_READ_ONLY_IF_AVAILABLE,
           PASSIVE_PARSER_CONTROL, NO_METABOLISM_CONTROL,
           NO_ONTOGENESIS_CONTROL, NO_SEMIOGENESIS_CONTROL,
           NO_COGNITION_CONTROL, NO_DESIRE_ACTION_CONTROL,
           RANDOMIZED_EVENT_ORDER, SILENCE_DEPRIVATION_CONDITION,
           OVERLOAD_CONDITION)


# Conditions that require a live read-only source (and therefore governance).
_LIVE_CONDITIONS = (ReplicationCondition.LIVE_READ_ONLY_IF_AVAILABLE,)


@dataclass
class ReplicationConstraint:
    """A named, rationalized constraint on the whole replication plan."""

    name: str
    value: Any
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "value": self.value,
                "rationale": self.rationale}


@dataclass
class ReplicationArm:
    """One condition's worth of source artifacts + comparison metadata."""

    arm_id: str
    condition: str
    purpose: str = ""
    source_artifacts: List[str] = field(default_factory=list)
    run_state_dir: str = ""
    soak_dossier_path: str = ""
    developmental_report_path: str = ""
    sensorium_profile: str = "fixture"
    seed: Optional[int] = None
    fixture_live_replay: str = "fixture"
    required_modules: List[str] = field(default_factory=list)
    optional_modules: List[str] = field(default_factory=list)
    max_comparison_scope: str = "artifact_comparison"
    requires_governance: bool = False
    safety_constraints: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "arm_id": self.arm_id, "condition": self.condition,
            "purpose": self.purpose,
            "source_artifacts": list(self.source_artifacts),
            "run_state_dir": self.run_state_dir,
            "soak_dossier_path": self.soak_dossier_path,
            "developmental_report_path": self.developmental_report_path,
            "sensorium_profile": self.sensorium_profile, "seed": self.seed,
            "fixture_live_replay": self.fixture_live_replay,
            "required_modules": list(self.required_modules),
            "optional_modules": list(self.optional_modules),
            "max_comparison_scope": self.max_comparison_scope,
            "requires_governance": self.requires_governance,
            "safety_constraints": list(self.safety_constraints),
            "limitations": list(self.limitations),
        }

    @classmethod
    def for_condition(cls, condition: str, *, arm_id: Optional[str] = None,
                      **kw) -> "ReplicationArm":
        live = condition in _LIVE_CONDITIONS
        sensorium = {
            ReplicationCondition.HUMAN_LIKE_ONLY: "human_like",
            ReplicationCondition.NON_HUMAN_ONLY: "non_human",
            ReplicationCondition.MIXED_PLURAL_SENSORIUM: "mixed",
            ReplicationCondition.FEATURE_ONLY: "feature_only",
        }.get(condition, "fixture")
        return cls(
            arm_id=arm_id or condition, condition=condition,
            purpose=f"compare developmental structure under {condition}",
            sensorium_profile=sensorium,
            fixture_live_replay="live" if live else "fixture",
            requires_governance=live,
            safety_constraints=["bounded artifact comparison; no unbounded soak",
                                "no feeder/hardware control; live needs "
                                "governance"],
            limitations=["compares observable structures only; not life or "
                         "consciousness"],
            **kw)


@dataclass
class ReplicationPlan:
    """A staged set of replication arms + constraints (compare, do not run)."""

    plan_id: str = "cross_run_developmental_replication"
    description: str = ("compare independent developmental runs across seeds, "
                        "sensorium diets, controls, and falsification cases")
    arms: Dict[str, ReplicationArm] = field(default_factory=dict)
    constraints: List[ReplicationConstraint] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.arms:
            self.arms = {c: ReplicationArm.for_condition(c)
                         for c in ReplicationCondition.ALL}
        if not self.constraints:
            self.constraints = default_constraints()

    @classmethod
    def default(cls) -> "ReplicationPlan":
        return cls()

    def arm(self, arm_id: str) -> ReplicationArm:
        if arm_id not in self.arms:
            raise KeyError(f"unknown replication arm {arm_id!r}")
        return self.arms[arm_id]

    def live_arms(self) -> List[str]:
        return [aid for aid, a in self.arms.items() if a.requires_governance]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id, "description": self.description,
            "arm_count": len(self.arms),
            "arms": {aid: self.arms[aid].to_dict()
                     for aid in sorted(self.arms)},
            "live_arms": sorted(self.live_arms()),
            "constraints": [c.to_dict() for c in self.constraints],
            "note": ("replication compares observable developmental structures "
                     "across independent runs; it does not prove life, "
                     "consciousness, sentience, personhood, agency, or free "
                     "will"),
        }


def default_constraints() -> List[ReplicationConstraint]:
    return [
        ReplicationConstraint("compares_existing_artifacts_by_default", True,
                              "the plan reads artifacts; it does not run soaks"),
        ReplicationConstraint("no_unbounded_soaks", True,
                              "replication never launches an unbounded soak"),
        ReplicationConstraint("short_bounded_demos_only", True,
                              "any run is a short bounded replication demo"),
        ReplicationConstraint("live_comparisons_require_governance", True,
                              "live read-only arms need governance approval"),
        ReplicationConstraint("missing_arms_inconclusive", True,
                              "a missing arm is unavailable/inconclusive, not "
                              "a crash"),
    ]
