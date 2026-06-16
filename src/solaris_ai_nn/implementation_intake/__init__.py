"""Implementation intake -- audit completed external implementations.

Prompt 57 generated implementation packs for external coding agents; Prompt 58
validates the completed implementations. The intake layer ingests local
artifacts (the compiler's prompt pack / branch spec / test matrix / safety gates /
review packet / rollback + validation plans, plus the implementation's summary,
diff/patch, changed-file list, test/example/ClaimGuard/safety-invariant results,
and optional PR metadata) and produces:

    diff audit -> spec compliance -> test audit -> safety regression ->
    ClaimGuard audit -> coverage matrix -> merge recommendation ->
    rollback recommendation -> post-merge validation plan

This is *not* a merge bot and *not* a coding agent. It is an evidence auditor. It
reads local artifacts and writes advisory reports only: it modifies no source,
executes no merge, creates/approves no pull request, calls no GitHub, runs no
Git, runs no external coding agent, runs no shell/network/browser/OS, never
approves itself, and makes no claim of consciousness, sentience, life,
personhood, agency, free will, emotion, feeling, understanding, or subjective
experience. Failed, missing, and falsified evidence is always preserved.
"""

from __future__ import annotations

from .artifact_reader import (
    ArtifactIntegrityIssue,
    ArtifactReadResult,
    ImplementationArtifactReader,
)
from .claimguard_audit import ClaimGuardAudit, ClaimGuardFinding, ClaimGuardStatus
from .coverage_matrix import (
    CoverageMatrixRow,
    CoverageStatus,
    ImplementationCoverageMatrix,
    build_coverage_matrix,
)
from .diff_audit import (
    ChangedFileAssessment,
    DiffAudit,
    DiffAuditFinding,
    DiffSeverity,
)
from .intake_manifest import (
    ImplementationArtifact,
    ImplementationArtifactStatus,
    ImplementationIntakeManifest,
)
from .intake_runtime import ImplementationIntakeRuntime
from .merge_recommendation import (
    MergeBlocker,
    MergeRecommendation,
    MergeRecommendationBuilder,
    MergeRecommendationStatus,
)
from .post_merge_plan import (
    PostMergeExitCriterion,
    PostMergeStageId,
    PostMergeValidationPlan,
    PostMergeValidationStage,
    build_post_merge_plan,
)
from .reports import ImplementationIntakeReportBuilder
from .rollback_recommendation import (
    RollbackRecommendation,
    RollbackRecommendationBuilder,
    RollbackRecommendationReason,
    RollbackUrgency,
)
from .safety import HARD_RULES, ImplementationIntakeSafetyValidator
from .safety_regression import (
    SafetyRegressionAudit,
    SafetyRegressionFinding,
    SafetyRegressionSeverity,
)
from .spec_compliance import (
    SpecComplianceAudit,
    SpecComplianceItem,
    SpecComplianceStatus,
)
from .test_result_audit import (
    TestFailureSummary,
    TestResultAudit,
    TestRunRecord,
)

__all__ = [
    "ImplementationIntakeManifest", "ImplementationArtifact",
    "ImplementationArtifactStatus",
    "ImplementationArtifactReader", "ArtifactReadResult",
    "ArtifactIntegrityIssue",
    "DiffAudit", "DiffAuditFinding", "ChangedFileAssessment", "DiffSeverity",
    "SpecComplianceAudit", "SpecComplianceItem", "SpecComplianceStatus",
    "TestResultAudit", "TestRunRecord", "TestFailureSummary",
    "SafetyRegressionAudit", "SafetyRegressionFinding",
    "SafetyRegressionSeverity",
    "ClaimGuardAudit", "ClaimGuardFinding", "ClaimGuardStatus",
    "ImplementationCoverageMatrix", "CoverageMatrixRow", "CoverageStatus",
    "build_coverage_matrix",
    "MergeRecommendation", "MergeRecommendationStatus", "MergeBlocker",
    "MergeRecommendationBuilder",
    "RollbackRecommendation", "RollbackRecommendationReason", "RollbackUrgency",
    "RollbackRecommendationBuilder",
    "PostMergeValidationPlan", "PostMergeValidationStage",
    "PostMergeExitCriterion", "PostMergeStageId", "build_post_merge_plan",
    "ImplementationIntakeRuntime",
    "ImplementationIntakeReportBuilder",
    "HARD_RULES", "ImplementationIntakeSafetyValidator",
]
