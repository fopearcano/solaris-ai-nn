"""Month-scale developmental soak protocol -- study, not life.

Prompt 53 implemented the Long-Horizon Developmental Runtime (the *engine* that
detects structural change over time). This package implements the formal
month-scale *study protocol* around it:

    preflight -> 2h dry run -> 24h trial -> 7d stabilization -> 30d soak ->
    optional 90d extension -> post-run autopsy

with daily evidence packets, weekly developmental reviews, restart drills,
corruption/source-silence drills, safety invariant checks, growth-vs-accumulation
checks, control-arm comparisons, an evidence dossier, and a final post-run
autopsy. The central question is: *did Solaris undergo measurable structural
development through autonomous sensorium-native experience?* -- not "did it
become conscious / understand / become alive / become an agent?".

The Developmental Life runtime remains the growth detector; this package is
protocol orchestration and evidence compilation only. Every invocation is
bounded (no unbounded daemon); long runs are reached by repeated bounded runs +
checkpoints. Nothing here starts feeders, controls hardware, touches the
network/shell/browser/OS, modifies a source, uses a human teaching loop, or
makes a claim of biological life, consciousness, sentience, personhood, agency,
free will, emotion, feeling, understanding, or subjective experience.
"""

from __future__ import annotations

from .checkpointing import (
    CheckpointIntegrityResult,
    CheckpointManager,
    SoakCheckpoint,
)
from .control_arms import (
    ControlArmConfig,
    ControlArmId,
    ControlArmResult,
    SoakControlArm,
)
from .daily_packet import DailyEvidencePacket, DailyEvidencePacketBuilder
from .evidence_dossier import (
    DevelopmentalEvidenceDossier,
    EvidenceClaim,
    EvidenceClaimType,
    EvidenceDossierBuilder,
    EvidenceStrength,
)
from .post_run_autopsy import (
    AutopsyFinding,
    AutopsyQuestion,
    AutopsyRecommendation,
    AutopsyResult,
    PostRunAutopsy,
)
from .preflight import (
    PreflightCheck,
    PreflightResult,
    PreflightStatus,
    SoakPreflight,
)
from .reports import DevelopmentalSoakReportBuilder
from .restart_drills import (
    RestartDrill,
    RestartDrillResult,
    RestartDrillRunner,
    RestartDrillType,
    RestartRecoveryAssessment,
)
from .run_phases import (
    SoakPhaseFailure,
    SoakPhaseState,
    SoakPhaseTransition,
    SoakRunPhase,
)
from .safety import HARD_RULES, DevelopmentalSoakSafetyValidator
from .soak_plan import (
    DevelopmentalSoakPlan,
    SoakPlanConstraint,
    SoakPlanProfile,
    SoakPlanStage,
    SoakPlanStageId,
    SourcePolicy,
)
from .soak_runtime import DevelopmentalSoakRuntime
from .weekly_review import (
    WeeklyDevelopmentalReview,
    WeeklyReviewBuilder,
    WeeklyReviewDecision,
)

__all__ = [
    "DevelopmentalSoakPlan", "SoakPlanProfile", "SoakPlanStage",
    "SoakPlanConstraint", "SoakPlanStageId", "SourcePolicy",
    "SoakPreflight", "PreflightCheck", "PreflightResult", "PreflightStatus",
    "SoakRunPhase", "SoakPhaseState", "SoakPhaseTransition", "SoakPhaseFailure",
    "CheckpointManager", "SoakCheckpoint", "CheckpointIntegrityResult",
    "DailyEvidencePacket", "DailyEvidencePacketBuilder",
    "WeeklyDevelopmentalReview", "WeeklyReviewBuilder", "WeeklyReviewDecision",
    "RestartDrill", "RestartDrillResult", "RestartDrillRunner",
    "RestartDrillType", "RestartRecoveryAssessment",
    "SoakControlArm", "ControlArmConfig", "ControlArmResult", "ControlArmId",
    "DevelopmentalEvidenceDossier", "EvidenceDossierBuilder", "EvidenceClaim",
    "EvidenceClaimType", "EvidenceStrength",
    "PostRunAutopsy", "AutopsyQuestion", "AutopsyResult", "AutopsyFinding",
    "AutopsyRecommendation",
    "DevelopmentalSoakRuntime",
    "DevelopmentalSoakReportBuilder",
    "HARD_RULES", "DevelopmentalSoakSafetyValidator",
]
