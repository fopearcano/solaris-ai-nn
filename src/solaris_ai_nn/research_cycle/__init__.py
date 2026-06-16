"""Closed research cycle orchestrator -- track the scientific state across cycles.

Prompt 60 creates a versioned research baseline. Prompt 61 is the closed research
cycle manager. It does not run the system autonomously, implement code changes,
approve anything, or execute external tools. It tracks the scientific state of the
project across cycles:

    Research Baseline -> Next-Cycle Roadmap -> Architecture Evolution Proposal
    -> Experiment Compiler Pack -> External Human/Agent Implementation
    -> Implementation Intake Audit -> Human Merge Outside Solaris
    -> Post-Merge Assimilation -> New Research Baseline
    -> Soak / Replication / Falsification -> Next Architecture Evolution

It answers: *where is the research program in its experimental cycle, what
evidence supports the current state, what is blocked, and what should the human
operator do next?* via an append-only evidence ledger, an artifact graph,
decision gates, operator-decision requirements, blocked states, next-action
recommendations, and a cycle archive.

It reads local artifacts and writes local metadata/reports only: it modifies no
source, runs no Git, calls no GitHub, creates no branch/tag/release/PR, opens or
merges no PR, executes no validation command, runs no external agent, controls no
feeders/hardware/network/shell, never approves itself, and makes no claim of
consciousness, sentience, life, personhood, agency, free will, emotion, feeling,
understanding, or subjective experience.
"""

from __future__ import annotations

from .artifact_graph import (
    ArtifactEdge,
    ArtifactEdgeType,
    ArtifactGraphBuilder,
    ArtifactNode,
    ArtifactNodeType,
    ResearchArtifactGraph,
)
from .blocked_states import (
    BlockedReason,
    BlockedStateResolver,
    ResearchCycleBlockedState,
    ResolverRecommendation,
)
from .cycle_archive import (
    ArchivedCycleRecord,
    ArchiveReason,
    ResearchCycleArchive,
)
from .cycle_manifest import (
    ResearchCycleArtifact,
    ResearchCycleIdentity,
    ResearchCycleManifest,
    ResearchCycleScope,
)
from .cycle_runtime import ResearchCycleRuntime
from .cycle_state import (
    ResearchCycleStage,
    ResearchCycleStageStatus,
    ResearchCycleState,
    determine_state,
)
from .cycle_transitions import (
    CycleTransitionEngine,
    ResearchCycleTransition,
    TransitionCondition,
)
from .decision_gates import (
    DecisionGateResult,
    DecisionGateStatus,
    DecisionGateType,
    ResearchCycleDecisionGate,
)
from .evidence_ledger import (
    EvidenceContinuityLedger,
    EvidenceContinuityStatus,
    EvidenceLedgerEntry,
    EvidenceLedgerEntryType,
)
from .next_action import (
    NextActionPlanner,
    NextActionPriority,
    NextActionType,
    ResearchCycleNextAction,
)
from .operator_decisions import (
    OperatorDecisionRecord,
    OperatorDecisionRequirement,
    OperatorDecisionStatus,
    OperatorDecisionType,
    load_operator_decisions,
    required_decisions,
)
from .reports import ResearchCycleReportBuilder
from .safety import HARD_RULES, ResearchCycleSafetyValidator

__all__ = [
    "ResearchCycleManifest", "ResearchCycleIdentity", "ResearchCycleArtifact",
    "ResearchCycleScope",
    "ResearchCycleState", "ResearchCycleStage", "ResearchCycleStageStatus",
    "determine_state",
    "ResearchCycleDecisionGate", "DecisionGateType", "DecisionGateResult",
    "DecisionGateStatus",
    "EvidenceContinuityLedger", "EvidenceLedgerEntry",
    "EvidenceLedgerEntryType", "EvidenceContinuityStatus",
    "ResearchArtifactGraph", "ArtifactNode", "ArtifactEdge",
    "ArtifactGraphBuilder", "ArtifactNodeType", "ArtifactEdgeType",
    "OperatorDecisionRecord", "OperatorDecisionType", "OperatorDecisionStatus",
    "OperatorDecisionRequirement", "load_operator_decisions",
    "required_decisions",
    "ResearchCycleTransition", "CycleTransitionEngine", "TransitionCondition",
    "ResearchCycleBlockedState", "BlockedReason", "BlockedStateResolver",
    "ResolverRecommendation",
    "ResearchCycleNextAction", "NextActionType", "NextActionPriority",
    "NextActionPlanner",
    "ResearchCycleArchive", "ArchivedCycleRecord", "ArchiveReason",
    "ResearchCycleRuntime",
    "ResearchCycleReportBuilder",
    "HARD_RULES", "ResearchCycleSafetyValidator",
]
