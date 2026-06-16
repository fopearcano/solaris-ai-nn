"""Live read-only birth protocol -- the first safe path from fixture to real input.

Prompts 41-66 built and documented a fixture-only research architecture. Prompt 67
opens the first safe path from fixture-only Alpha to real environmental input -- the
"birth" layer. Birth means: real environment -> external read-only feeders -> JSONL
inbox spool -> validator -> quarantine if unsafe -> sensory membrane -> perceptual
metabolism -> alpha/live report -> birth certificate.

Solaris never controls the source: it only reads event files written by external
feeder scripts. The layer is local-only, bounded, inspectable, and reversible. It
does not start/stop/control feeders, control hardware, access the network/shell/
browser/OS/camera/microphone, call Git/GitHub, execute commands, modify source,
treat sensory text as a command, treat human labels or debug gloss as ground truth,
or make any claim of consciousness, sentience, biological life, personhood, agency,
free will, emotion, feeling, understanding, self-awareness, autonomous
self-improvement, or subjective experience. The birth certificate is operational,
not biological.
"""

from __future__ import annotations

from .birth_certificate import BirthCertificate, BirthCertificateBuilder
from .birth_profile import (
    ALLOWED_FIRST_BIRTH_SOURCES,
    DEFAULT_PROFILE_ID,
    FORBIDDEN_FIRST_BIRTH_SOURCES,
    LiveBirthConstraint,
    LiveBirthProfile,
    LiveBirthProfileMode,
    available_profiles,
    default_live_birth_profile,
    get_live_birth_profile,
)
from .birth_runtime import LiveReadOnlyBirthRuntime
from .event_schema import (
    LiveEventEnvelope,
    LiveEventQuality,
    LiveEventSafety,
    LiveEventSource,
    LiveSensoryEvent,
)
from .event_validator import (
    LiveEventValidationFinding,
    LiveEventValidationResult,
    LiveEventValidationSeverity,
    LiveEventValidator,
)
from .feeder_registry import (
    FeederStatus,
    FeederTrustLevel,
    LiveFeederRecord,
    LiveFeederRegistry,
    feeder_registry_template,
)
from .governance import (
    GovernanceRule,
    GovernanceStatus,
    GovernanceValidator,
    LiveReadOnlyGovernance,
    approved_governance,
    governance_template,
)
from .inbox_spool import InboxBatch, InboxReadResult, LiveInboxSpool
from .membrane_activation import (
    AcceptedLiveEventBatch,
    EnvironmentalMembraneActivation,
    MembraneActivationResult,
)
from .quarantine import QuarantineReason, QuarantineRecord, QuarantineStore
from .reports import LiveBirthReportBuilder
from .safety import HARD_RULES, LiveBirthSafetyValidator

__all__ = [
    "LiveBirthProfile", "LiveBirthProfileMode", "LiveBirthConstraint",
    "default_live_birth_profile", "get_live_birth_profile",
    "available_profiles", "DEFAULT_PROFILE_ID", "ALLOWED_FIRST_BIRTH_SOURCES",
    "FORBIDDEN_FIRST_BIRTH_SOURCES",
    "LiveReadOnlyGovernance", "GovernanceRule", "GovernanceStatus",
    "GovernanceValidator", "governance_template", "approved_governance",
    "LiveFeederRegistry", "LiveFeederRecord", "FeederStatus", "FeederTrustLevel",
    "feeder_registry_template",
    "LiveSensoryEvent", "LiveEventQuality", "LiveEventSafety", "LiveEventSource",
    "LiveEventEnvelope",
    "LiveEventValidator", "LiveEventValidationResult",
    "LiveEventValidationFinding", "LiveEventValidationSeverity",
    "LiveInboxSpool", "InboxBatch", "InboxReadResult",
    "QuarantineRecord", "QuarantineStore", "QuarantineReason",
    "EnvironmentalMembraneActivation", "MembraneActivationResult",
    "AcceptedLiveEventBatch",
    "LiveReadOnlyBirthRuntime",
    "BirthCertificate", "BirthCertificateBuilder",
    "LiveBirthReportBuilder",
    "HARD_RULES", "LiveBirthSafetyValidator",
]
