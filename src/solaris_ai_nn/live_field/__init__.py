"""Live field -- real read-only environmental flux for the plural sensorium.

Prompt 42 exposed Solaris to *fixture* feeders. This package is the first real
read-only environmental field pilot: external feeders (separate operator-run
processes) write Sensory Event Envelopes into local files and folders, and Solaris
reads them through the plural sensorium. The flow is one-directional --

    outside world -> external feeder -> local event envelope files ->
    read-only sensory membrane -> plural sensorium receptors ->
    continuous sensory field -> Stimulus / Push / Desire -> internal adaptation

Solaris reads; it does not control. Nothing here accesses hardware, an SDR, a
microphone/camera, the network, or a shell; nothing starts a feeder, modifies,
deletes, or moves a source file, decodes private communications, treats sensory
text as a command, or performs real-world actuation. Live mode requires governance
approval, and no claim of consciousness, sentience, life, personhood, agency, or
free will is made.
"""

from __future__ import annotations

from .comparison import LiveFieldComparison, LiveFieldComparisonResult
from .external_dropbox import (
    INBOX_MODALITIES,
    FeatureDropbox,
    FeatureDropboxIngestor,
    FeatureDropboxPollResult,
)
from .feeder_contract import (
    LiveFeederContract,
    LiveFeederEnvelope,
    LiveFeederEvent,
    LiveFeederMode,
    LiveFeederTrust,
)
from .feeder_registry import (
    LiveFeederDescriptor,
    LiveFeederRegistry,
    LiveFeederStatus,
)
from .live_field_pilot import (
    LiveFieldPilot,
    LiveFieldPilotConfig,
    LiveFieldPilotPhase,
    LiveFieldPilotResult,
)
from .live_field_report import LiveFieldReportBuilder
from .live_field_runtime import LiveFieldRuntime
from .live_field_trace import (
    LiveFieldTrace,
    LiveFieldTraceEvent,
    LiveFieldTraceEventType,
)
from .local_feeders import (
    FeatureDropboxFeederValidator,
    FeederValidationResult,
    ManualLogFeederValidator,
    SystemRhythmFeederValidator,
    WatchedFolderFeederValidator,
)
from .safety import HARD_RULES, LiveFieldSafetyValidator
from .source_health import (
    SourceHealthEvent,
    SourceHealthMonitor,
    SourceHealthState,
)

__all__ = [
    "LiveFieldComparison", "LiveFieldComparisonResult",
    "INBOX_MODALITIES", "FeatureDropbox", "FeatureDropboxIngestor",
    "FeatureDropboxPollResult",
    "LiveFeederContract", "LiveFeederEnvelope", "LiveFeederEvent",
    "LiveFeederMode", "LiveFeederTrust",
    "LiveFeederDescriptor", "LiveFeederRegistry", "LiveFeederStatus",
    "LiveFieldPilot", "LiveFieldPilotConfig", "LiveFieldPilotPhase",
    "LiveFieldPilotResult",
    "LiveFieldReportBuilder", "LiveFieldRuntime",
    "LiveFieldTrace", "LiveFieldTraceEvent", "LiveFieldTraceEventType",
    "FeatureDropboxFeederValidator", "FeederValidationResult",
    "ManualLogFeederValidator", "SystemRhythmFeederValidator",
    "WatchedFolderFeederValidator",
    "HARD_RULES", "LiveFieldSafetyValidator",
    "SourceHealthEvent", "SourceHealthMonitor", "SourceHealthState",
]
