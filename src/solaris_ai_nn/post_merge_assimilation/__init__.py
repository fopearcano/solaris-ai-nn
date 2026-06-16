"""Post-merge evidence assimilation -- the research ledger after a human merge.

Prompt 58 audits implementation artifacts and recommends merge/revision/block.
Prompt 59 handles the post-merge research state *after a human operator has
merged or otherwise accepted an implementation outside Solaris*:

    merge manifest -> ingest validation -> assimilate evidence ->
    register candidate baseline -> compare to parent -> regression watch ->
    module status + rollback recommendations -> follow-up queue -> reports

It answers one question from local operator-provided evidence: "a human changed
the code externally -- what did that change do to the experimental organismic
architecture?". This is *not* a merge bot, a release system, or self-modification.

It reads local artifacts and writes local metadata/reports only: it runs no Git,
calls no GitHub, creates/approves/merges no pull request, modifies no source,
executes no validation command, runs no external coding agent, controls no
feeders/hardware/network/shell, and makes no claim of consciousness, sentience,
life, personhood, agency, free will, emotion, feeling, understanding, or
subjective experience. The baseline registry is append-only; a safety regression
dominates positive metrics; and failed/missing/falsified evidence is preserved.
"""

from __future__ import annotations

from .baseline_comparison import (
    BaselineComparison,
    BaselineComparisonDimension,
    BaselineComparisonResult,
    BaselineComparisonStatus,
)
from .baseline_registry import (
    BaselineEvidenceIndex,
    BaselineRecord,
    BaselineRegistry,
    BaselineStatus,
)
from .evidence_assimilation import (
    AssimilatedEvidenceBundle,
    EvidenceAssimilationFinding,
    EvidenceVerdict,
    PostMergeEvidenceAssimilator,
)
from .followup_queue import (
    FollowupItem,
    FollowupItemType,
    FollowupPriority,
    FollowupStatus,
    PostMergeFollowupQueue,
    build_followup_queue,
)
from .merge_manifest import (
    MergeArtifact,
    MergeConfirmation,
    MergeSourceType,
    PostMergeManifest,
)
from .module_status_update import (
    ModuleStatusUpdateReason,
    ModuleStatusUpdateRecommendation,
    ModuleStatusUpdateRecommendationBuilder,
    ModuleStatusUpdateType,
)
from .post_merge_runtime import PostMergeAssimilationRuntime
from .regression_watch import (
    RegressionWatch,
    RegressionWatchCategory,
    RegressionWatchItem,
    RegressionWatchResult,
    RegressionWatchSeverity,
)
from .reports import PostMergeAssimilationReportBuilder
from .rollback_watch import (
    RollbackWatch,
    RollbackWatchRecommendation,
    RollbackWatchResult,
    RollbackWatchTrigger,
)
from .safety import HARD_RULES, PostMergeAssimilationSafetyValidator
from .validation_ingest import (
    PostMergeValidationIngest,
    ValidationArtifact,
    ValidationArtifactType,
    ValidationIngestResult,
)

__all__ = [
    "PostMergeManifest", "MergeConfirmation", "MergeArtifact", "MergeSourceType",
    "BaselineRegistry", "BaselineRecord", "BaselineStatus",
    "BaselineEvidenceIndex",
    "PostMergeEvidenceAssimilator", "AssimilatedEvidenceBundle",
    "EvidenceAssimilationFinding", "EvidenceVerdict",
    "BaselineComparison", "BaselineComparisonResult",
    "BaselineComparisonDimension", "BaselineComparisonStatus",
    "RegressionWatch", "RegressionWatchItem", "RegressionWatchSeverity",
    "RegressionWatchResult", "RegressionWatchCategory",
    "ModuleStatusUpdateRecommendation", "ModuleStatusUpdateRecommendationBuilder",
    "ModuleStatusUpdateType", "ModuleStatusUpdateReason",
    "PostMergeValidationIngest", "ValidationArtifact", "ValidationIngestResult",
    "ValidationArtifactType",
    "RollbackWatch", "RollbackWatchTrigger", "RollbackWatchRecommendation",
    "RollbackWatchResult",
    "PostMergeFollowupQueue", "FollowupItem", "FollowupPriority",
    "FollowupStatus", "FollowupItemType", "build_followup_queue",
    "PostMergeAssimilationRuntime",
    "PostMergeAssimilationReportBuilder",
    "HARD_RULES", "PostMergeAssimilationSafetyValidator",
]
