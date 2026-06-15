"""External feeders -- the origin of environmental flux, never Solaris's hands.

An external feeder is any separate process, device, script, logger, recorder, or
human-maintained stream that writes feature events into local files. A
:class:`ExternalFeederDescriptor` *describes* such an origin; it does not give
Solaris any control over the hardware or the recorder. Solaris only ever reads
the feeder's output.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class FeederSourceType:
    MANUAL_LOG = "manual_log"
    LOCAL_SCRIPT = "local_script"
    SENSOR_LOGGER = "sensor_logger"
    SDR_FEATURE_EXPORTER = "sdr_feature_exporter"
    RADAR_METADATA_EXPORTER = "radar_metadata_exporter"
    THERMAL_FEATURE_EXPORTER = "thermal_feature_exporter"
    VIBRATION_LOGGER = "vibration_logger"
    MAGNETIC_LOGGER = "magnetic_logger"
    SYSTEM_METRICS_LOGGER = "system_metrics_logger"
    FOLDER_DROP = "folder_drop"
    FIXTURE_REPLAY = "fixture_replay"
    UNKNOWN_EXTERNAL = "unknown_external"

    ALL = (MANUAL_LOG, LOCAL_SCRIPT, SENSOR_LOGGER, SDR_FEATURE_EXPORTER,
           RADAR_METADATA_EXPORTER, THERMAL_FEATURE_EXPORTER, VIBRATION_LOGGER,
           MAGNETIC_LOGGER, SYSTEM_METRICS_LOGGER, FOLDER_DROP, FIXTURE_REPLAY,
           UNKNOWN_EXTERNAL)
    # Source types that describe real, outside-world hardware/processes. These
    # require governance approval before the runtime reads them for real.
    REAL_WORLD = frozenset({SENSOR_LOGGER, SDR_FEATURE_EXPORTER,
                            RADAR_METADATA_EXPORTER, THERMAL_FEATURE_EXPORTER,
                            VIBRATION_LOGGER, MAGNETIC_LOGGER})


class FeederTrustLevel:
    UNTRUSTED = "untrusted"
    FIXTURE = "fixture"
    MANUAL = "manual"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    ALL = (UNTRUSTED, FIXTURE, MANUAL, LOW, MEDIUM, HIGH)


@dataclass
class ExternalFeederDescriptor:
    """Describes one external feeder. It never grants Solaris control."""

    feeder_id: str
    source_type: str
    path: str
    modality_hint: str = ""
    trust_level: str = FeederTrustLevel.FIXTURE
    is_real_world: bool = False
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Structural guarantees -- the feeder is read-only and not controllable.
    read_only: bool = True
    controllable_by_solaris: bool = False

    def __post_init__(self) -> None:
        if self.source_type not in FeederSourceType.ALL:
            self.source_type = FeederSourceType.UNKNOWN_EXTERNAL
        if self.trust_level not in FeederTrustLevel.ALL:
            self.trust_level = FeederTrustLevel.UNTRUSTED
        # Solaris never controls a feeder; it only reads its output.
        self.read_only = True
        self.controllable_by_solaris = False
        if self.source_type in FeederSourceType.REAL_WORLD:
            self.is_real_world = True
        if self.source_type == FeederSourceType.FIXTURE_REPLAY:
            self.is_real_world = False

    @property
    def requires_governance(self) -> bool:
        return self.is_real_world

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feeder_id": self.feeder_id,
            "source_type": self.source_type,
            "path": self.path,
            "modality_hint": self.modality_hint,
            "trust_level": self.trust_level,
            "is_real_world": self.is_real_world,
            "requires_governance": self.requires_governance,
            "description": self.description,
            "read_only": True,
            "controllable_by_solaris": False,
            "metadata": dict(self.metadata),
        }


def fixture_feeder(feeder_id: str, path: str, modality_hint: str = "",
                   source_type: str = FeederSourceType.FIXTURE_REPLAY,
                   ) -> ExternalFeederDescriptor:
    """Convenience: a fixture/replay feeder (safe by default, no governance)."""
    return ExternalFeederDescriptor(
        feeder_id=feeder_id, source_type=source_type, path=path,
        modality_hint=modality_hint, trust_level=FeederTrustLevel.FIXTURE)
