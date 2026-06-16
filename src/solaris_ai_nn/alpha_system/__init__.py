"""Alpha Research System -- the unified, bounded, local operator entry point.

Prompts 41-64 created many organismic, scientific, governance, review, and
claim-control layers. Prompt 65 assembles them into a coherent local Alpha Research
System so an operator can run one bounded command and watch Solaris-AI-NN move
through a coherent research path: from fixture sensorium input to an alpha report,
scientific claims, review readiness, and a next action.

It is not a new cognition theory layer -- it makes the system operable. It provides
a bounded fixture-only profile, a module registry, a state layout, a doctor
(system check), an end-to-end demo plan, an orchestrator, an artifact index, a
cycle status, an operator runbook, reports, and a safety validator. The runtime is
local-only and bounded: it does not actuate, control hardware/feeders, access the
network/shell/browser/OS, call Git/GitHub, create branches/tags/releases/PRs,
upload/publish, run external agents, modify source, or make any claim of
consciousness, sentience, biological life, personhood, agency, free will, emotion,
feeling, understanding, self-awareness, or subjective experience.
"""

from __future__ import annotations

from .alpha_orchestrator import AlphaResearchOrchestrator
from .alpha_profile import (
    DEFAULT_PROFILE_ID,
    AlphaProfileConstraint,
    AlphaProfileMode,
    AlphaResearchProfile,
    available_profiles,
    default_alpha_profile,
    get_alpha_profile,
)
from .artifact_index import (
    AlphaArtifactIndex,
    AlphaArtifactKind,
    AlphaArtifactRecord,
)
from .cycle_status import (
    AlphaCycleStage,
    AlphaCycleStatus,
    AlphaNextAction,
    determine_cycle_status,
)
from .demo_plan import AlphaDemoPlan, AlphaDemoStep, AlphaDemoStepStatus
from .module_registry import (
    AlphaModuleRecord,
    AlphaModuleRegistry,
    AlphaModuleStatus,
)
from .operator_runbook import (
    AlphaOperatorRunbook,
    AlphaRunbookBuilder,
    AlphaRunbookStep,
)
from .reports import AlphaResearchReportBuilder
from .safety import HARD_RULES, AlphaResearchSafetyValidator
from .state_layout import (
    DEFAULT_STATE_ROOT,
    AlphaArtifactPath,
    AlphaStateDirectory,
    AlphaStateLayout,
)
from .system_check import (
    AlphaCheckResult,
    AlphaCheckSeverity,
    AlphaSystemCheck,
)

__all__ = [
    "AlphaResearchProfile", "AlphaProfileMode", "AlphaProfileConstraint",
    "default_alpha_profile", "get_alpha_profile", "available_profiles",
    "DEFAULT_PROFILE_ID",
    "AlphaModuleRegistry", "AlphaModuleRecord", "AlphaModuleStatus",
    "AlphaStateLayout", "AlphaStateDirectory", "AlphaArtifactPath",
    "DEFAULT_STATE_ROOT",
    "AlphaSystemCheck", "AlphaCheckResult", "AlphaCheckSeverity",
    "AlphaDemoPlan", "AlphaDemoStep", "AlphaDemoStepStatus",
    "AlphaResearchOrchestrator",
    "AlphaArtifactIndex", "AlphaArtifactRecord", "AlphaArtifactKind",
    "AlphaCycleStatus", "AlphaCycleStage", "AlphaNextAction",
    "determine_cycle_status",
    "AlphaOperatorRunbook", "AlphaRunbookStep", "AlphaRunbookBuilder",
    "AlphaResearchReportBuilder",
    "HARD_RULES", "AlphaResearchSafetyValidator",
]
