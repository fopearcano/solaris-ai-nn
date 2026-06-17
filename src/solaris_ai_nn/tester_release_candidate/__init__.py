"""Tester release candidate assembly, manifest, bundle, and readiness gate (P80).

This package assembles the first local trusted-tester release candidate. It collects the
install guide, quickstart, runbook, release notes, known issues, safety boundaries, claim
freeze, red-team checklist, release blocker report, fixture/live-read-only instructions,
external feeder policy, feedback forms, console instructions, artifact manifest, final RC
checklist, readiness report, and a local tester bundle.

It is a local assembly step only. It never publishes, uploads, tags, releases, or sends
anything anywhere. It never installs packages, starts/executes feeders, controls
hardware, accesses the network/shell/Git/GitHub/browser/OS, opens a browser, starts a
background service, modifies source, executes artifact contents, trains on tester
feedback, allows raw-event or membrane bypass, or makes a claim of consciousness,
sentience, biological life, personhood, agency, free will, emotion, feeling,
understanding, self-awareness, autonomous self-improvement, autonomous intent, autonomous
desire, or real-world autonomy.
"""

from __future__ import annotations

from .rc_artifact_collector import (
    CollectedRCArtifact,
    RCArtifactCollectionResult,
    RCArtifactTier,
    TesterRCArtifactCollector,
)
from .rc_bundle_builder import (
    TesterRCBundle,
    TesterRCBundleBuilder,
    TesterRCBundleManifest,
)
from .rc_checklist import (
    RCChecklistItem,
    RCChecklistStatus,
    RCChecklistTier,
    TesterRCChecklist,
)
from .rc_manifest import (
    TesterRCArtifact,
    TesterRCManifest,
    TesterRCManifestBuilder,
    TesterRCStatus,
)
from .rc_notes_builder import (
    TesterFeedbackGuideBuilder,
    TesterKnownIssuesBuilder,
    TesterReleaseNotesBuilder,
)
from .rc_profile import (
    DEFAULT_PROFILE_ID,
    TesterRCConstraint,
    TesterRCMode,
    TesterRCProfile,
    available_profiles,
    default_rc_profile,
    get_rc_profile,
)
from .rc_readiness_gate import (
    RCReadinessBlocker,
    RCReadinessResult,
    RCReadinessStatus,
    RCReadinessWarning,
    TesterRCReadinessGate,
)
from .rc_runbook_builder import RunbookSection, RunbookStep, TesterRunbookBuilder
from .rc_runtime import TesterRCRuntime
from .reports import TesterRCReportBuilder
from .safety import HARD_RULES, TesterRCSafetyValidator

__all__ = [
    "HARD_RULES", "TesterRCSafetyValidator",
    "TesterRCProfile", "TesterRCMode", "TesterRCConstraint",
    "default_rc_profile", "get_rc_profile", "available_profiles",
    "DEFAULT_PROFILE_ID",
    "TesterRCManifest", "TesterRCManifestBuilder", "TesterRCArtifact",
    "TesterRCStatus",
    "TesterRCArtifactCollector", "CollectedRCArtifact",
    "RCArtifactCollectionResult", "RCArtifactTier",
    "TesterRCReadinessGate", "RCReadinessResult", "RCReadinessBlocker",
    "RCReadinessWarning", "RCReadinessStatus",
    "TesterReleaseNotesBuilder", "TesterKnownIssuesBuilder",
    "TesterFeedbackGuideBuilder",
    "TesterRunbookBuilder", "RunbookStep", "RunbookSection",
    "TesterRCBundle", "TesterRCBundleBuilder", "TesterRCBundleManifest",
    "TesterRCChecklist", "RCChecklistItem", "RCChecklistStatus",
    "RCChecklistTier",
    "TesterRCRuntime", "TesterRCReportBuilder",
]
