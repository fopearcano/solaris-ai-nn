"""Independent reproducibility review -- a local, offline peer-audit preparation.

Prompt 62 created a scientific claim registry and publication-grade evidence
dossier. Prompt 63 prepares a local, offline, independent review package. It
answers: *what evidence can an external reviewer inspect, what commands would
reproduce the bounded demos, what artifacts are required or missing, what claims
are reviewable or blocked, what falsification tests and controls should a reviewer
run, what questions should a hostile reviewer ask, what objections have been
raised, what responses exist, and what remains unresolved?*

It is a local preparation layer for independent reproducibility and critique -- not
publishing, not external submission, not a marketing kit, and not an automatic
peer-review system. It indexes local artifacts, scans them for sanitization and
forbidden-claim risks (without modifying them), builds a reviewer pack,
reproducibility challenges, a review protocol, hostile reviewer questions,
adversarial alternative explanations, an audit matrix, an append-only response
ledger, and a review-readiness report. It never publishes, uploads, contacts
reviewers, calls Git/GitHub or external APIs, executes commands or experiments,
runs external agents, controls feeders/hardware/network/shell, or makes any claim
of consciousness, sentience, biological life, personhood, agency, free will,
emotion, feeling, understanding, self-awareness, autonomous self-improvement, or
subjective experience.
"""

from __future__ import annotations

from .adversarial_review import (
    AdversarialReviewEngine,
    AdversarialReviewFinding,
    AlternativeExplanation,
    AlternativeExplanationType,
)
from .artifact_sanitizer import (
    ReviewArtifactSanitizer,
    SanitizationFinding,
    SanitizationFindingType,
    SanitizationReport,
    SanitizationStatus,
)
from .audit_matrix import (
    AuditMatrixRow,
    AuditMatrixStatus,
    IndependentReviewAuditMatrix,
)
from .response_ledger import (
    ObjectionStatus,
    ReviewerObjection,
    ReviewerResponse,
    ReviewerResponseLedger,
    load_objections,
)
from .review_manifest import (
    ARTIFACT_CATEGORIES,
    IndependentReviewManifest,
    ReviewArtifact,
    ReviewArtifactStatus,
    ReviewScope,
)
from .review_protocol import (
    IndependentReviewProtocol,
    ReviewProtocolExitCriteria,
    ReviewProtocolStage,
    ReviewProtocolStageType,
)
from .review_readiness import (
    IndependentReviewReadiness,
    IndependentReviewReadinessEvaluator,
    ReviewReadinessBlocker,
    ReviewReadinessStatus,
)
from .review_runtime import IndependentReviewRuntime
from .reviewer_pack import (
    IndependentReviewerPack,
    ReviewerPackBuilder,
    ReviewerPackSection,
)
from .reviewer_questions import (
    ReviewerQuestion,
    ReviewerQuestionCategory,
    ReviewerQuestionGenerator,
)
from .reproducibility_challenge import (
    ChallengeExpectedResult,
    ChallengeStatus,
    ChallengeStep,
    ChallengeType,
    ReproducibilityChallenge,
    ReproducibilityChallengeBuilder,
)
from .reports import IndependentReviewReportBuilder
from .safety import HARD_RULES, IndependentReviewSafetyValidator

__all__ = [
    "IndependentReviewManifest", "ReviewArtifact", "ReviewArtifactStatus",
    "ReviewScope", "ARTIFACT_CATEGORIES",
    "ReviewArtifactSanitizer", "SanitizationFinding", "SanitizationFindingType",
    "SanitizationReport", "SanitizationStatus",
    "IndependentReviewerPack", "ReviewerPackBuilder", "ReviewerPackSection",
    "ReproducibilityChallenge", "ReproducibilityChallengeBuilder",
    "ChallengeStep", "ChallengeExpectedResult", "ChallengeStatus",
    "ChallengeType",
    "IndependentReviewProtocol", "ReviewProtocolStage",
    "ReviewProtocolStageType", "ReviewProtocolExitCriteria",
    "ReviewerQuestion", "ReviewerQuestionCategory", "ReviewerQuestionGenerator",
    "AdversarialReviewEngine", "AdversarialReviewFinding",
    "AlternativeExplanation", "AlternativeExplanationType",
    "IndependentReviewAuditMatrix", "AuditMatrixRow", "AuditMatrixStatus",
    "ReviewerResponseLedger", "ReviewerObjection", "ReviewerResponse",
    "ObjectionStatus", "load_objections",
    "IndependentReviewReadiness", "IndependentReviewReadinessEvaluator",
    "ReviewReadinessStatus", "ReviewReadinessBlocker",
    "IndependentReviewRuntime",
    "IndependentReviewReportBuilder",
    "HARD_RULES", "IndependentReviewSafetyValidator",
]
