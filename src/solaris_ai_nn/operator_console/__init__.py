"""Operator console -- one local, file-backed layer to inspect, plan, and run.

Solaris-AI-NN has many subsystems (conscience, pilots, sensory/motor membranes,
safety invariants, research lab, post-pilot forensics, architecture evolution,
evaluation, governance, ops, Inner MAP). This package is the single operator-
facing layer that lets a human safely inspect, plan, run, compare, and audit
them.

It is not a chatbot, not an autonomous agent, not an approval bypass, and not a
GUI-heavy application. It is a local, low-compute, file-backed console. Its core
principle is simple: the console can *coordinate*, but it cannot grant forbidden
authority. It launches only bounded allowed profiles, and only through the
conscience orchestrator; it runs no shell and makes no network calls; it cannot
bypass governance, safety invariants, emergency stop, ClaimGuard, the motor
firewall, the sensory read-only boundary, or architecture-evolution safety; its
approval records can never enable prohibited real-world actuation; and it makes
no claim of consciousness, life, sentience, agency, personhood, or free will.
"""

from __future__ import annotations

from .approval_ledger import (
    ApprovalLedger,
    ApprovalRecord,
    ApprovalScope,
    ApprovalStatus,
)
from .artifact_index import (
    ArtifactIndex,
    ArtifactIndexer,
    ArtifactRecord,
)
from .console_config import (
    ConsoleAuthority,
    ConsoleMode,
    OperatorConsoleConfig,
)
from .decision_board import (
    DecisionCategory,
    DecisionItem,
    DecisionStatus,
    OperatorDecisionBoard,
)
from .evidence_navigator import (
    EvidenceNavigator,
    EvidenceQuery,
    EvidenceSearchResult,
    EvidenceType,
)
from .export_bundle import (
    BUNDLE_TYPES,
    ExportBundle,
    ExportBundleBuilder,
)
from .next_action import (
    NextActionPriority,
    NextActionRecommendation,
    NextActionRecommender,
    NextActionType,
)
from .operator_queries import (
    OperatorQueryResult,
    OperatorQueryRouter,
    SUPPORTED_QUERIES,
)
from .profile_catalog import (
    ProfileCatalog,
    ProfileCatalogEntry,
    ProfileSafetyClass,
)
from .report_index import (
    ReportIndex,
    ReportIndexer,
    ReportRecord,
)
from .run_launcher import (
    LaunchBlocker,
    RunLauncher,
    RunLaunchResult,
)
from .run_planner import (
    RunPlan,
    RunPlanStep,
    RunPlanValidation,
    RunPlanner,
)
from .safety import (
    HARD_RULES,
    OperatorConsoleSafetyValidator,
)
from .session_log import (
    OperatorSessionEvent,
    OperatorSessionEventType,
    OperatorSessionLog,
)
from .status_board import (
    OperatorStatusBoard,
    StatusBoardSnapshot,
)

__all__ = [
    "ApprovalLedger", "ApprovalRecord", "ApprovalScope", "ApprovalStatus",
    "ArtifactIndex", "ArtifactIndexer", "ArtifactRecord",
    "ConsoleAuthority", "ConsoleMode", "OperatorConsoleConfig",
    "DecisionCategory", "DecisionItem", "DecisionStatus",
    "OperatorDecisionBoard",
    "EvidenceNavigator", "EvidenceQuery", "EvidenceSearchResult",
    "EvidenceType",
    "BUNDLE_TYPES", "ExportBundle", "ExportBundleBuilder",
    "NextActionPriority", "NextActionRecommendation", "NextActionRecommender",
    "NextActionType",
    "OperatorQueryResult", "OperatorQueryRouter", "SUPPORTED_QUERIES",
    "ProfileCatalog", "ProfileCatalogEntry", "ProfileSafetyClass",
    "ReportIndex", "ReportIndexer", "ReportRecord",
    "LaunchBlocker", "RunLauncher", "RunLaunchResult",
    "RunPlan", "RunPlanStep", "RunPlanValidation", "RunPlanner",
    "HARD_RULES", "OperatorConsoleSafetyValidator",
    "OperatorSessionEvent", "OperatorSessionEventType", "OperatorSessionLog",
    "OperatorStatusBoard", "StatusBoardSnapshot",
]
