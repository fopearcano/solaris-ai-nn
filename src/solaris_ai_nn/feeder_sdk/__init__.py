"""External feeder SDK -- the safe outside layer that feeds Solaris perception.

A feeder is an *artificial sensory organ* outside Solaris. It converts a real
environmental phenomenon (RF spectrum features, echo reflections, vibration,
thermal gradients, magnetic field, human-like text/light/temperature, machine
rhythm, absence) into validated :class:`FeederSDKEnvelope` records that Solaris
reads read-only:

    outside world -> external feeder / sensory organ -> local event envelope
    stream -> Solaris read-only live field -> plural sensorium receptors ->
    sensory field -> internal adaptation

This SDK provides the contract, writer utilities, modality schemas, validators,
privacy filters, replay tools, clock/noise helpers, feeder blueprints, a feeder
pack manifest, and an output monitor. The feeder is outside Solaris and Solaris
reads only: nothing here lets Solaris start, stop, configure, or command a feeder
or any hardware; nothing requires the network or a shell; nothing ingests decoded
private communications or raw audio/video by default; human labels are never
ground truth; sensory text is never a command; and no claim of consciousness,
sentience, life, personhood, agency, or free will is made.
"""

from __future__ import annotations

from .blueprints import (
    BlueprintStatus,
    FeederBlueprint,
    FeederBlueprintRegistry,
)
from .clock import FeederClock, JitterModel, TickSchedule
from .contract import (
    SCHEMA_VERSION,
    FeederSDKAnnotationStatus,
    FeederSDKEnvelope,
    FeederSDKEvent,
    FeederSDKModality,
    FeederSDKSource,
    FeederSDKTrustLevel,
)
from .monitor import (
    FeederMonitor,
    FeederMonitorSnapshot,
    FeederOutputHealth,
)
from .noise import BurstModel, DriftModel, DropoutModel, FeatureNoiseModel
from .packager import FeederPack, FeederPackBuilder, FeederPackManifest
from .privacy import PrivacyFilter, PrivacyFlag, PrivacyReport, PrivacyRisk
from .replay import FeederReplay, ReplayClock, ReplayResult
from .safety import HARD_RULES, FeederSDKSafetyValidator
from .schemas import (
    FEATURE_SCHEMAS,
    FeatureSchema,
    all_event_types,
    get_schema,
    schema_coverage,
    schema_for_modality,
)
from .validators import (
    EnvelopeValidator,
    FeederOutputValidator,
    SchemaValidator,
    ValidationIssue,
    ValidationResult,
)
from .writer import (
    EnvelopeWriter,
    FeederWriteResult,
    JSONLFeederWriter,
    RollingJSONLFeederWriter,
)

__all__ = [
    "BlueprintStatus", "FeederBlueprint", "FeederBlueprintRegistry",
    "FeederClock", "JitterModel", "TickSchedule",
    "SCHEMA_VERSION", "FeederSDKAnnotationStatus", "FeederSDKEnvelope",
    "FeederSDKEvent", "FeederSDKModality", "FeederSDKSource",
    "FeederSDKTrustLevel",
    "FeederMonitor", "FeederMonitorSnapshot", "FeederOutputHealth",
    "BurstModel", "DriftModel", "DropoutModel", "FeatureNoiseModel",
    "FeederPack", "FeederPackBuilder", "FeederPackManifest",
    "PrivacyFilter", "PrivacyFlag", "PrivacyReport", "PrivacyRisk",
    "FeederReplay", "ReplayClock", "ReplayResult",
    "HARD_RULES", "FeederSDKSafetyValidator",
    "FEATURE_SCHEMAS", "FeatureSchema", "all_event_types", "get_schema",
    "schema_coverage", "schema_for_modality",
    "EnvelopeValidator", "FeederOutputValidator", "SchemaValidator",
    "ValidationIssue", "ValidationResult",
    "EnvelopeWriter", "FeederWriteResult", "JSONLFeederWriter",
    "RollingJSONLFeederWriter",
]
