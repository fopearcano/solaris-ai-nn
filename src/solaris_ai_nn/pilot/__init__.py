"""Pilot-0: governed, supervised, bounded deployment profiles.

Three sanctioned shapes -- ``simulated`` (the default, fully internal),
``read_only_stream`` (local JSONL/text files become sensory stimuli; the
world is read, never touched), and ``solaris_sidecar_observe`` (observe a
Solaris_Ai-like bus; suggestions only). Every pilot is bounded unless
explicitly approved through governance, gated by the PilotSafetyValidator,
run under the OperationalSupervisor, and accounted for with readiness
reports, registry entries, and ClaimGuard-scanned pilot reports. This is
controlled deployment, not autonomy.
"""

from .adapters import (  # noqa: F401
    ReadOnlyStreamPilotAdapter,
    SimulatedPilotAdapter,
    SolarisSidecarPilotAdapter,
)
from .data_contracts import (  # noqa: F401
    MAX_PAYLOAD_CHARS,
    ValidationResult,
    normalize_event,
    validate_jsonl_event,
    validate_text_line,
)
from .deployment_runner import PilotDeploymentRunner  # noqa: F401
from .pilot_manifest import (  # noqa: F401
    PilotEnvironment,
    PilotManifest,
    PilotSafetyContract,
)
from .pilot_registry import PilotRegistry  # noqa: F401
from .pilot_report import (  # noqa: F401
    PilotRecommendation,
    PilotReportBuilder,
    recommend,
)
from .profiles import (  # noqa: F401
    PilotProfile,
    PilotProfileRegistry,
    PilotProfileType,
)
from .readiness import (  # noqa: F401
    PilotReadinessCheck,
    PilotReadinessReport,
    ReadinessIssue,
)
from .safety import PilotSafetyValidator, SafetyReport  # noqa: F401
from .stream_ingestion import ReadOnlyStreamIngestor  # noqa: F401
from .stream_sensors import (  # noqa: F401
    JsonlStreamSensor,
    SilenceWindowSensor,
    SyntheticHeartbeatSensor,
    TextStreamSensor,
    build_stream_sensor,
    event_to_stimulus,
)

__all__ = [
    "PilotProfile", "PilotProfileType", "PilotProfileRegistry",
    "PilotManifest", "PilotEnvironment", "PilotSafetyContract",
    "ValidationResult", "validate_jsonl_event", "validate_text_line",
    "normalize_event", "MAX_PAYLOAD_CHARS",
    "ReadOnlyStreamIngestor",
    "JsonlStreamSensor", "TextStreamSensor", "SyntheticHeartbeatSensor",
    "SilenceWindowSensor", "build_stream_sensor", "event_to_stimulus",
    "PilotSafetyValidator", "SafetyReport",
    "PilotDeploymentRunner",
    "PilotReadinessCheck", "PilotReadinessReport", "ReadinessIssue",
    "PilotReportBuilder", "PilotRecommendation", "recommend",
    "PilotRegistry",
    "SimulatedPilotAdapter", "ReadOnlyStreamPilotAdapter",
    "SolarisSidecarPilotAdapter",
]
