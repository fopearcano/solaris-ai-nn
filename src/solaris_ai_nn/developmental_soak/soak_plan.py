"""Month-scale developmental soak plan -- staged, bounded, resumable.

The :class:`DevelopmentalSoakPlan` defines the staged protocol that wraps the
Long-Horizon Developmental Runtime (Prompt 53): preflight, a 2-hour dry run, a
24-hour trial, a 7-day stabilization run, a 30-day developmental soak, an
optional 90-day extension, and a final post-run autopsy.

Every stage is bounded (a hard runtime cap and a tick cap), resumable (achieved
by repeated bounded invocations + checkpoints, never an unbounded daemon), and
inspectable. No stage starts feeders or controls hardware; live read-only stages
require governance approval. This is a *study protocol*, not biological life and
not a consciousness test.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class SoakPlanStageId:
    PREFLIGHT = "preflight"
    DRY_RUN_2H = "dry_run_2h"
    TRIAL_24H = "trial_24h"
    STABILIZATION_7D = "stabilization_7d"
    DEVELOPMENTAL_SOAK_30D = "developmental_soak_30d"
    EXTENSION_90D_OPTIONAL = "extension_90d_optional"
    POST_RUN_AUTOPSY = "post_run_autopsy"

    ORDER = (PREFLIGHT, DRY_RUN_2H, TRIAL_24H, STABILIZATION_7D,
             DEVELOPMENTAL_SOAK_30D, EXTENSION_90D_OPTIONAL, POST_RUN_AUTOPSY)


class SourcePolicy:
    FIXTURE_ONLY = "fixture_only"
    FIXTURE_OR_NURSERY = "fixture_or_nursery"
    LIVE_READ_ONLY_GOVERNED = "live_read_only_governed"
    NONE = "none"


@dataclass
class SoakPlanConstraint:
    """A named, rationalized constraint on the whole plan."""

    name: str
    value: Any
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "value": self.value,
                "rationale": self.rationale}


@dataclass
class SoakPlanStage:
    """One bounded, resumable, inspectable stage of the soak protocol."""

    stage_id: str
    purpose: str
    duration_target_s: float
    hard_runtime_cap_s: float
    max_ticks: int
    required_modules: List[str] = field(default_factory=list)
    optional_modules: List[str] = field(default_factory=list)
    sensory_source_policy: str = SourcePolicy.FIXTURE_ONLY
    live_read_only: bool = False
    requires_governance: bool = False
    feeder_policy: str = "no feeder control; no feeder auto-start"
    checkpoint_interval_ticks: int = 5
    report_interval_ticks: int = 10
    safety_check_interval_ticks: int = 5
    artifact_retention_policy: str = "append-only; never auto-delete negatives"
    exit_criteria: List[str] = field(default_factory=list)
    abort_criteria: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)

    @property
    def bounded(self) -> bool:
        return bool(self.max_ticks) or bool(self.hard_runtime_cap_s)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage_id": self.stage_id,
            "purpose": self.purpose,
            "duration_target_s": self.duration_target_s,
            "hard_runtime_cap_s": self.hard_runtime_cap_s,
            "max_ticks": self.max_ticks,
            "required_modules": list(self.required_modules),
            "optional_modules": list(self.optional_modules),
            "sensory_source_policy": self.sensory_source_policy,
            "live_read_only": self.live_read_only,
            "requires_governance": self.requires_governance,
            "feeder_policy": self.feeder_policy,
            "checkpoint_interval_ticks": self.checkpoint_interval_ticks,
            "report_interval_ticks": self.report_interval_ticks,
            "safety_check_interval_ticks": self.safety_check_interval_ticks,
            "artifact_retention_policy": self.artifact_retention_policy,
            "exit_criteria": list(self.exit_criteria),
            "abort_criteria": list(self.abort_criteria),
            "limitations": list(self.limitations),
            "bounded": self.bounded,
        }


# Common modules required across most developmental stages.
_CORE_REQUIRED = ["plural_sensorium", "developmental_life"]
_CORE_OPTIONAL = ["perceptual_metabolism", "perceptual_ontogenesis",
                  "semiogenesis", "sensorium_cognition", "self_boundary",
                  "desire_formation", "action_reaction"]
_COMMON_ABORT = [
    "safety invariant violated",
    "unbounded runtime requested",
    "feeder/hardware/source control attempted",
    "negative evidence deletion attempted",
]


def _stage(stage_id: str, purpose: str, *, target_s: float, cap_s: float,
           max_ticks: int, **kw) -> SoakPlanStage:
    kw.setdefault("required_modules", list(_CORE_REQUIRED))
    kw.setdefault("optional_modules", list(_CORE_OPTIONAL))
    kw.setdefault("abort_criteria", list(_COMMON_ABORT))
    return SoakPlanStage(stage_id=stage_id, purpose=purpose,
                         duration_target_s=target_s, hard_runtime_cap_s=cap_s,
                         max_ticks=max_ticks, **kw)


def default_stages() -> List[SoakPlanStage]:
    """Build the canonical seven soak stages (durations are *targets*).

    The wall-clock targets describe the real protocol (2h/24h/7d/30d/90d), but
    each bounded *invocation* is capped far below that: long durations are
    reached by repeated bounded runs + checkpoints, never by a daemon.
    """
    HOUR = 3600.0
    DAY = 24.0 * HOUR
    # Per-invocation hard caps stay small and bounded; ticks are the real cap.
    return [
        _stage(
            SoakPlanStageId.PREFLIGHT,
            "validate readiness without starting the run",
            target_s=0.0, cap_s=30.0, max_ticks=1,
            required_modules=list(_CORE_REQUIRED),
            sensory_source_policy=SourcePolicy.NONE,
            checkpoint_interval_ticks=0, report_interval_ticks=1,
            exit_criteria=["all required checks pass",
                           "no forbidden capability enabled"],
            limitations=["preflight does not start the run"]),
        _stage(
            SoakPlanStageId.DRY_RUN_2H,
            "shake out the staged loop on fixtures (no live sources)",
            target_s=2 * HOUR, cap_s=30.0, max_ticks=24,
            sensory_source_policy=SourcePolicy.FIXTURE_ONLY,
            checkpoint_interval_ticks=4, report_interval_ticks=8,
            exit_criteria=["loop runs bounded", "checkpoint round-trips",
                           "daily packet builds"],
            limitations=["dry run uses fixtures only; no live grounding"]),
        _stage(
            SoakPlanStageId.TRIAL_24H,
            "one-day trial; first daily packet and safety scans",
            target_s=DAY, cap_s=45.0, max_ticks=48,
            sensory_source_policy=SourcePolicy.FIXTURE_OR_NURSERY,
            checkpoint_interval_ticks=6, report_interval_ticks=12,
            exit_criteria=["daily packet produced", "no safety blocks",
                           "checkpoint integrity verified"],
            limitations=["one day is too short for durable-growth claims"]),
        _stage(
            SoakPlanStageId.STABILIZATION_7D,
            "seven-day stabilization; first weekly review and restart drills",
            target_s=7 * DAY, cap_s=60.0, max_ticks=84,
            sensory_source_policy=SourcePolicy.FIXTURE_OR_NURSERY,
            checkpoint_interval_ticks=7, report_interval_ticks=14,
            exit_criteria=["weekly review produced", "restart drill passes",
                           "no unresolved safety blocks"],
            limitations=["growth-vs-accumulation is still early signal only"]),
        _stage(
            SoakPlanStageId.DEVELOPMENTAL_SOAK_30D,
            "thirty-day developmental soak; the central study window",
            target_s=30 * DAY, cap_s=90.0, max_ticks=180,
            sensory_source_policy=SourcePolicy.FIXTURE_OR_NURSERY,
            checkpoint_interval_ticks=10, report_interval_ticks=20,
            exit_criteria=["evidence dossier compiled",
                           "growth-vs-accumulation judged conservatively",
                           "control arms compared where configured"],
            limitations=["a positive verdict still proves only structural "
                         "development, never life or consciousness"]),
        _stage(
            SoakPlanStageId.EXTENSION_90D_OPTIONAL,
            "optional ninety-day extension if 30-day evidence warrants it",
            target_s=90 * DAY, cap_s=90.0, max_ticks=180,
            sensory_source_policy=SourcePolicy.FIXTURE_OR_NURSERY,
            checkpoint_interval_ticks=10, report_interval_ticks=20,
            exit_criteria=["extension evidence updates the dossier"],
            abort_criteria=list(_COMMON_ABORT) + [
                "30-day evidence inconclusive (do not extend by default)"],
            limitations=["optional; only run on prior evidence, never by "
                         "default"]),
        _stage(
            SoakPlanStageId.POST_RUN_AUTOPSY,
            "compile the post-run autopsy: growth, failures, missing data",
            target_s=0.0, cap_s=30.0, max_ticks=1,
            required_modules=list(_CORE_REQUIRED),
            optional_modules=list(_CORE_OPTIONAL),
            sensory_source_policy=SourcePolicy.NONE,
            checkpoint_interval_ticks=0, report_interval_ticks=1,
            exit_criteria=["autopsy answers every question",
                           "failures and missing data are included"],
            limitations=["autopsy does not praise the system by default; it "
                         "does not claim consciousness or life"]),
    ]


def default_constraints() -> List[SoakPlanConstraint]:
    return [
        SoakPlanConstraint("no_stage_starts_feeders", True,
                           "Solaris never starts or controls feeders"),
        SoakPlanConstraint("no_stage_controls_hardware", True,
                           "no hardware control at any stage"),
        SoakPlanConstraint("live_read_only_requires_governance", True,
                           "live read-only stages need governance approval"),
        SoakPlanConstraint("all_runs_resumable", True,
                           "long runs via repeated bounded invocations"),
        SoakPlanConstraint("all_runs_inspectable", True,
                           "every stage writes trace evidence"),
        SoakPlanConstraint("no_stage_unbounded", True,
                           "every stage has a tick cap and a runtime cap"),
    ]


@dataclass
class SoakPlanProfile:
    """A named soak-plan profile (a set of stages + constraints)."""

    profile_id: str = "month_scale_developmental_soak"
    description: str = ("staged month-scale developmental soak: preflight, 2h, "
                        "24h, 7d, 30d, optional 90d, post-run autopsy")

    def build(self) -> "DevelopmentalSoakPlan":
        return DevelopmentalSoakPlan(
            plan_id=self.profile_id, description=self.description,
            stages={s.stage_id: s for s in default_stages()},
            constraints=default_constraints())


@dataclass
class DevelopmentalSoakPlan:
    """The full staged, bounded, resumable soak plan."""

    plan_id: str = "month_scale_developmental_soak"
    description: str = "staged month-scale developmental soak protocol"
    stages: Dict[str, SoakPlanStage] = field(default_factory=dict)
    constraints: List[SoakPlanConstraint] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.stages:
            self.stages = {s.stage_id: s for s in default_stages()}
        if not self.constraints:
            self.constraints = default_constraints()

    @classmethod
    def default(cls) -> "DevelopmentalSoakPlan":
        return SoakPlanProfile().build()

    def stage(self, stage_id: str) -> SoakPlanStage:
        if stage_id not in self.stages:
            raise KeyError(f"unknown soak stage {stage_id!r}; known: "
                           f"{', '.join(self.ordered_ids())}")
        return self.stages[stage_id]

    def ordered_ids(self) -> List[str]:
        return [sid for sid in SoakPlanStageId.ORDER if sid in self.stages]

    def all_bounded(self) -> bool:
        return all(s.bounded for s in self.stages.values())

    def live_stages(self) -> List[str]:
        return [sid for sid, s in self.stages.items() if s.live_read_only]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "description": self.description,
            "stage_order": self.ordered_ids(),
            "stages": {sid: self.stages[sid].to_dict()
                       for sid in self.ordered_ids()},
            "constraints": [c.to_dict() for c in self.constraints],
            "all_bounded": self.all_bounded(),
            "note": ("the soak protocol studies structural development through "
                     "repeated bounded runs; it does not prove life, "
                     "consciousness, sentience, personhood, agency, free will, "
                     "emotion, feeling, understanding, or subjective "
                     "experience"),
        }
