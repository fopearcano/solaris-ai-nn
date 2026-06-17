"""Tester release safety freeze, claim freeze, red-team, and release blocker gate (P79).

This package is the tester-release safety firewall. Before assembling the first tester
release candidate, it gates on forbidden capabilities, forbidden claims, unsafe wording,
missing disclaimers, membrane bypass, raw-event bypass, feeder-control risks, hardware/
network/shell/Git/GitHub risks, privacy risks, feedback-as-training risks, install/
doctor/tester-demo blockers, fixture reproducibility blockers, live-read-only governance
blockers, console/report overclaiming, missing safety docs, and missing tester warnings.

It is not a new research layer. It is report/gate-only and local: it scans only local
text artifacts and executes nothing. It never starts feeders, controls hardware,
accesses the network/shell/browser/OS/Git/GitHub, publishes/uploads, creates releases/
tags/issues, opens a browser, trains on feedback, modifies runtime behaviour, or makes a
claim of consciousness, sentience, biological life, personhood, agency, free will,
emotion, feeling, understanding, self-awareness, autonomous self-improvement, autonomous
intent, autonomous desire, or real-world autonomy. The safety freeze does NOT prove the
system safe in general; it is a tester-release gate only.
"""

from __future__ import annotations

from .allowed_language import (
    AllowedOperationalLanguageRegistry,
    AllowedPhrase,
    ReplacementSuggestion,
)
from .artifact_safety_scan import (
    ArtifactSafetyFinding,
    ArtifactSafetyScanResult,
    TesterArtifactSafetyScan,
)
from .capability_freeze import (
    CapabilityCategory,
    CapabilityFinding,
    CapabilityFreezeResult,
    TesterCapabilityFreeze,
)
from .claim_freeze import (
    ClaimFinding,
    ClaimFreezeResult,
    ClaimSeverity,
    TesterClaimFreeze,
)
from .forbidden_claims import (
    ForbiddenClaim,
    ForbiddenClaimCategory,
    ForbiddenClaimPattern,
    ForbiddenClaimRegistry,
)
from .red_team_checklist import (
    RedTeamCategory,
    RedTeamCheck,
    RedTeamCheckResult,
    RedTeamStatus,
    TesterRedTeamChecklist,
)
from .release_blockers import (
    ReleaseBlocker,
    ReleaseBlockerCategory,
    ReleaseBlockerStatus,
    TesterReleaseBlockerGate,
)
from .reports import TesterSafetyFreezeReportBuilder
from .safety import HARD_RULES, TesterSafetyFreezeSafetyValidator
from .safety_freeze_manifest import (
    SafetyFreezeManifestBuilder,
    SafetyFreezeStatus,
    TesterSafetyFreezeManifest,
)
from .safety_freeze_profile import (
    DEFAULT_PROFILE_ID,
    TesterSafetyFreezeConstraint,
    TesterSafetyFreezeMode,
    TesterSafetyFreezeProfile,
    available_profiles,
    default_safety_freeze_profile,
    get_safety_freeze_profile,
)
from .safety_freeze_runtime import TesterSafetyFreezeRuntime

__all__ = [
    "HARD_RULES", "TesterSafetyFreezeSafetyValidator",
    "TesterSafetyFreezeProfile", "TesterSafetyFreezeMode",
    "TesterSafetyFreezeConstraint", "default_safety_freeze_profile",
    "get_safety_freeze_profile", "available_profiles", "DEFAULT_PROFILE_ID",
    "TesterClaimFreeze", "ClaimFreezeResult", "ClaimFinding", "ClaimSeverity",
    "ForbiddenClaimRegistry", "ForbiddenClaim", "ForbiddenClaimPattern",
    "ForbiddenClaimCategory",
    "AllowedOperationalLanguageRegistry", "AllowedPhrase",
    "ReplacementSuggestion",
    "TesterCapabilityFreeze", "CapabilityFreezeResult", "CapabilityFinding",
    "CapabilityCategory",
    "TesterRedTeamChecklist", "RedTeamCheck", "RedTeamCheckResult",
    "RedTeamCategory", "RedTeamStatus",
    "TesterReleaseBlockerGate", "ReleaseBlocker", "ReleaseBlockerStatus",
    "ReleaseBlockerCategory",
    "TesterArtifactSafetyScan", "ArtifactSafetyFinding",
    "ArtifactSafetyScanResult",
    "TesterSafetyFreezeManifest", "SafetyFreezeManifestBuilder",
    "SafetyFreezeStatus",
    "TesterSafetyFreezeRuntime", "TesterSafetyFreezeReportBuilder",
]
