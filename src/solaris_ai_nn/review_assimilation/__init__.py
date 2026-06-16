"""Reviewer feedback assimilation -- review feedback as research evidence.

Prompt 63 prepared a local independent review pack and a response ledger. Prompt 64
assimilates review feedback into the scientific and experimental cycle. It ingests
local reviewer objections, the response ledger, adversarial findings, audit-matrix
blockers, reproduction outcomes, sanitizer findings, the review-readiness report,
reviewer notes, failed/successful reproductions, missing-artifact reports, claim
objections, alternative explanations, and proposed reviewer experiments. It then
produces a feedback assimilation report, objection classification, claim and theory
impact assessments, an evidence gap map, experiment/ablation/falsification
recommendations, claim revision proposals, a publication-readiness revision, and a
next-cycle review queue.

This is scientific feedback assimilation into the research ledger -- NOT a Human
Feedback / Teaching Loop, NOT model training, NOT RLHF, and NOT public peer-review
automation. It reads local artifacts and writes local reports only; it never trains
on reviewer feedback, publishes, uploads, contacts reviewers, calls Git/GitHub or
external APIs, executes commands or experiments, runs external agents, controls
feeders/hardware/network/shell, or makes any claim of consciousness, sentience,
biological life, personhood, agency, free will, emotion, feeling, understanding,
self-awareness, autonomous self-improvement, or subjective experience.
"""

from __future__ import annotations

from .assimilation_runtime import ReviewerFeedbackAssimilationRuntime
from .claim_impact import (
    ClaimImpactAssessment,
    ClaimImpactAssessor,
    ClaimImpactSeverity,
    ClaimImpactType,
)
from .claim_revision import (
    ClaimRevisionProposal,
    ClaimRevisionProposer,
    ClaimRevisionStatus,
    ClaimRevisionType,
)
from .evidence_gap_map import (
    EvidenceGap,
    EvidenceGapCategory,
    EvidenceGapSeverity,
    ReviewEvidenceGapMap,
    ReviewEvidenceGapMapBuilder,
)
from .experiment_recommendations import (
    RecommendationPriority,
    RecommendationType,
    ReviewDrivenExperimentRecommendation,
    ReviewDrivenExperimentRecommender,
)
from .feedback_manifest import (
    FeedbackArtifactStatus,
    FeedbackSourceType,
    ReviewerFeedbackArtifact,
    ReviewerFeedbackManifest,
)
from .objection_classifier import (
    ObjectionCategory,
    ObjectionSeverity,
    ObjectionValidityStatus,
    ReviewerObjectionClassification,
    ReviewerObjectionClassifier,
)
from .publication_readiness_revision import (
    PublicationReadinessBlocker,
    PublicationReadinessImpact,
    PublicationReadinessReviser,
    PublicationReadinessRevision,
)
from .reports import ReviewerFeedbackAssimilationReportBuilder
from .reproduction_outcomes import (
    ReproductionFailureReason,
    ReproductionOutcomeStatus,
    ReviewerReproductionOutcome,
    ReviewerReproductionOutcomeIngestor,
)
from .review_queue import (
    ReviewAssimilationQueue,
    ReviewQueueItem,
    ReviewQueueItemType,
    ReviewQueuePriority,
    ReviewQueueStatus,
)
from .safety import (
    HARD_RULES,
    ReviewerFeedbackAssimilationSafetyValidator,
)
from .theory_impact import (
    TheoryImpactAssessment,
    TheoryImpactAssessor,
    TheoryImpactType,
)

__all__ = [
    "ReviewerFeedbackManifest", "ReviewerFeedbackArtifact",
    "FeedbackSourceType", "FeedbackArtifactStatus",
    "ReviewerObjectionClassifier", "ReviewerObjectionClassification",
    "ObjectionCategory", "ObjectionSeverity", "ObjectionValidityStatus",
    "ReviewerReproductionOutcomeIngestor", "ReviewerReproductionOutcome",
    "ReproductionOutcomeStatus", "ReproductionFailureReason",
    "ClaimImpactAssessor", "ClaimImpactAssessment", "ClaimImpactType",
    "ClaimImpactSeverity",
    "TheoryImpactAssessor", "TheoryImpactAssessment", "TheoryImpactType",
    "ReviewEvidenceGapMapBuilder", "ReviewEvidenceGapMap", "EvidenceGap",
    "EvidenceGapCategory", "EvidenceGapSeverity",
    "ReviewDrivenExperimentRecommender", "ReviewDrivenExperimentRecommendation",
    "RecommendationType", "RecommendationPriority",
    "ClaimRevisionProposer", "ClaimRevisionProposal", "ClaimRevisionType",
    "ClaimRevisionStatus",
    "PublicationReadinessReviser", "PublicationReadinessRevision",
    "PublicationReadinessImpact", "PublicationReadinessBlocker",
    "ReviewAssimilationQueue", "ReviewQueueItem", "ReviewQueueItemType",
    "ReviewQueueStatus", "ReviewQueuePriority",
    "ReviewerFeedbackAssimilationRuntime",
    "ReviewerFeedbackAssimilationReportBuilder",
    "HARD_RULES", "ReviewerFeedbackAssimilationSafetyValidator",
]
