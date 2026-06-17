"""Tester feedback forms, bug report intake, and non-training feedback ledger (P77).

A local tester QA ledger. Testers record install/CLI/fixture/live problems, membrane/
quarantine confusion, safety concerns, documentation/console confusion, unsupported-
claim concerns, performance issues, missing/unexpected artifacts, feeder/governance
issues, and suggestions. The feedback stays **local**, structured, append-only, and
reviewable by the developer; it is exportable only as a local bundle.

This is NOT the Human Feedback / Teaching Loop and NOT RLHF. Feedback is never training
data, never ground truth, never a command, and it never automatically modifies Solaris
behaviour (concepts, signs, cognition traces, membrane thresholds, governance, feeder
registry, or scientific claims). The runtime never creates remote issues, uploads/
publishes, accesses the network/shell/browser/OS/Git/GitHub, controls feeders/hardware,
executes feedback contents, or makes claims about consciousness, sentience, biological
life, personhood, agency, free will, emotion, feeling, understanding, self-awareness,
autonomous self-improvement, or subjective experience. Safety concerns are elevated as
release blockers (developer review items), and unsupported consciousness/life/agency
claim concerns are release blockers until reviewed.
"""

from __future__ import annotations

from .bug_report import (
    BugAffectedModule,
    BugReportBuilder,
    BugReportValidationResult,
    TesterBugReport,
)
from .confusion_report import (
    ConfusionArea,
    ConfusionSeverity,
    TesterConfusionReport,
)
from .feedback_bundle import (
    FeedbackBundleBuilder,
    FeedbackBundleManifest,
    TesterFeedbackBundle,
)
from .feedback_form import (
    FeedbackCategory,
    FeedbackQuestion,
    FeedbackSeverity,
    FeedbackSubmission,
    TesterFeedbackForm,
)
from .feedback_ledger import (
    FeedbackEntryStatus,
    FeedbackLedgerEntry,
    FeedbackLedgerIndex,
    TesterFeedbackLedger,
)
from .feedback_profile import (
    DEFAULT_PROFILE_ID,
    TesterFeedbackConstraint,
    TesterFeedbackMode,
    TesterFeedbackProfile,
    available_profiles,
    default_feedback_profile,
    get_feedback_profile,
)
from .feedback_runtime import TesterFeedbackRuntime
from .release_blocker_classifier import (
    ReleaseBlockerClassification,
    ReleaseBlockerClassifier,
    ReleaseBlockerReason,
    ReleaseBlockerStatus,
)
from .reports import TesterFeedbackReportBuilder
from .safety import HARD_RULES, TesterFeedbackSafetyValidator
from .safety_concern import (
    SafetyConcernEscalation,
    SafetyConcernType,
    TesterSafetyConcern,
)
from .suggestion_report import (
    SuggestionDisposition,
    SuggestionType,
    TesterSuggestionReport,
)

__all__ = [
    "HARD_RULES", "TesterFeedbackSafetyValidator",
    "TesterFeedbackProfile", "TesterFeedbackMode", "TesterFeedbackConstraint",
    "default_feedback_profile", "get_feedback_profile", "available_profiles",
    "DEFAULT_PROFILE_ID",
    "TesterFeedbackForm", "FeedbackQuestion", "FeedbackSubmission",
    "FeedbackCategory", "FeedbackSeverity",
    "TesterBugReport", "BugReportBuilder", "BugReportValidationResult",
    "BugAffectedModule",
    "TesterSafetyConcern", "SafetyConcernType", "SafetyConcernEscalation",
    "TesterConfusionReport", "ConfusionArea", "ConfusionSeverity",
    "TesterSuggestionReport", "SuggestionType", "SuggestionDisposition",
    "TesterFeedbackLedger", "FeedbackLedgerEntry", "FeedbackLedgerIndex",
    "FeedbackEntryStatus",
    "ReleaseBlockerClassifier", "ReleaseBlockerClassification",
    "ReleaseBlockerReason", "ReleaseBlockerStatus",
    "TesterFeedbackBundle", "FeedbackBundleBuilder", "FeedbackBundleManifest",
    "TesterFeedbackRuntime", "TesterFeedbackReportBuilder",
]
