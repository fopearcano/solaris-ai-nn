"""Versioned research baseline -- a local reproducible experimental reference.

Prompt 59 registers and watches a candidate post-merge baseline. Prompt 60 turns a
validated (or validated-with-warnings) baseline into a *versioned research
baseline*:

    baseline version -> snapshot manifest -> reproducibility bundle ->
    capability map -> limitation registry -> safety boundary statement ->
    validation summary -> comparison anchors -> next-cycle roadmap -> runbook

It answers one question: *what exact experimental baseline are we standing on
before the next cycle begins?* This is not a product release, a GitHub release, a
certification of consciousness or intelligence, or autonomous deployment -- it is
a reproducible research snapshot.

It writes local metadata/reports only: it creates no Git tag, GitHub release,
branch, or PR; calls no Git/GitHub; modifies no source; runs no validation
command; runs no external agent; controls no feeders/hardware/network/shell; and
makes no claim of consciousness, sentience, life, personhood, agency, free will,
emotion, feeling, understanding, or subjective experience. A blocked baseline
cannot become a validated version; a critical limitation or a failed safety
boundary blocks validation; and failed/missing/falsified evidence is preserved.
"""

from __future__ import annotations

from .baseline_runtime import ResearchBaselineRuntime
from .baseline_version import (
    BaselineVersionRecord,
    BaselineVersionStatus,
    ResearchBaselineVersion,
)
from .capability_map import (
    BaselineCapabilityMap,
    CapabilityRecord,
    CapabilityStatus,
)
from .comparison_anchors import (
    AnchorKind,
    ComparisonAnchor,
    ComparisonAnchorSet,
)
from .limitation_registry import (
    BaselineLimitation,
    BaselineLimitationRegistry,
    LimitationCategory,
    LimitationSeverity,
    build_limitation_registry,
)
from .operator_runbook import (
    BaselineOperatorRunbook,
    RunbookChecklist,
    RunbookStep,
    build_operator_runbook,
)
from .repro_bundle import (
    EvidenceProvenance,
    ReproBundleBuilder,
    ReproBundleIntegrityResult,
    ReproducibilityBundle,
)
from .reports import ResearchBaselineReportBuilder
from .roadmap_reset import (
    NextCycleRoadmapReset,
    RoadmapItem,
    RoadmapItemType,
    RoadmapPriority,
    RoadmapStatus,
    build_roadmap_reset,
)
from .safety import HARD_RULES, ResearchBaselineSafetyValidator
from .safety_boundary_statement import (
    SafetyBoundaryItem,
    SafetyBoundaryStatement,
    SafetyBoundaryStatus,
)
from .snapshot_manifest import (
    ResearchSnapshotManifest,
    SnapshotArtifact,
    SnapshotArtifactStatus,
)
from .validation_summary import (
    BaselineValidationSummary,
    ValidationDimension,
    ValidationStatus,
)

__all__ = [
    "ResearchBaselineVersion", "BaselineVersionStatus", "BaselineVersionRecord",
    "ResearchSnapshotManifest", "SnapshotArtifact", "SnapshotArtifactStatus",
    "ReproducibilityBundle", "ReproBundleBuilder", "ReproBundleIntegrityResult",
    "EvidenceProvenance",
    "BaselineCapabilityMap", "CapabilityRecord", "CapabilityStatus",
    "BaselineLimitationRegistry", "BaselineLimitation", "LimitationSeverity",
    "LimitationCategory", "build_limitation_registry",
    "SafetyBoundaryStatement", "SafetyBoundaryItem", "SafetyBoundaryStatus",
    "BaselineValidationSummary", "ValidationDimension", "ValidationStatus",
    "ComparisonAnchor", "ComparisonAnchorSet", "AnchorKind",
    "NextCycleRoadmapReset", "RoadmapItem", "RoadmapItemType",
    "RoadmapPriority", "RoadmapStatus", "build_roadmap_reset",
    "BaselineOperatorRunbook", "RunbookStep", "RunbookChecklist",
    "build_operator_runbook",
    "ResearchBaselineRuntime",
    "ResearchBaselineReportBuilder",
    "HARD_RULES", "ResearchBaselineSafetyValidator",
]
