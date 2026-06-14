"""Sensory source schema -- typed, read-only descriptions of input sources.

A :class:`SensorySourceConfig` describes one controlled, read-only source the
membrane may poll. All sources are read-only, must live inside explicitly
allowed input directories, are bounded (file size / events per poll), and
degrade gracefully when missing. No binary parsing beyond safe metadata.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


class SensorySourceType:
    JSONL_FILE = "jsonl_file"
    TEXT_FILE = "text_file"
    NUMERIC_CSV = "numeric_csv"
    FOLDER_SNAPSHOT = "folder_snapshot"
    FOLDER_POLL = "folder_poll"
    EVENT_LOG = "event_log"
    MANUAL_DUMP = "manual_dump"
    SIMULATED_CAMERA_METADATA = "simulated_camera_metadata"
    SIMULATED_AUDIO_METADATA = "simulated_audio_metadata"
    SYNTHETIC_SENSOR = "synthetic_sensor"
    UNKNOWN = "unknown"

    ALL = (JSONL_FILE, TEXT_FILE, NUMERIC_CSV, FOLDER_SNAPSHOT, FOLDER_POLL,
           EVENT_LOG, MANUAL_DUMP, SIMULATED_CAMERA_METADATA,
           SIMULATED_AUDIO_METADATA, SYNTHETIC_SENSOR, UNKNOWN)
    # Source types that are simulated (never a real external read).
    SIMULATED = frozenset({SIMULATED_CAMERA_METADATA,
                           SIMULATED_AUDIO_METADATA, SYNTHETIC_SENSOR,
                           MANUAL_DUMP})
    # Source types that read a real file/folder on disk (read-only).
    REAL_READ_ONLY = frozenset({JSONL_FILE, TEXT_FILE, NUMERIC_CSV,
                               FOLDER_SNAPSHOT, FOLDER_POLL, EVENT_LOG})


class SensorySourceStatus:
    REGISTERED = "registered"
    ACTIVE = "active"
    DEGRADED = "degraded"
    DISABLED = "disabled"
    MISSING = "missing"
    QUARANTINED = "quarantined"

    ALL = (REGISTERED, ACTIVE, DEGRADED, DISABLED, MISSING, QUARANTINED)


class TrustLevel:
    UNTRUSTED = "untrusted"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    ALL = (UNTRUSTED, LOW, MEDIUM, HIGH)


@dataclass
class SensorySourceConfig:
    """A read-only, bounded configuration for one sensory source."""

    source_id: str
    source_type: str = SensorySourceType.UNKNOWN
    path: Optional[str] = None
    enabled: bool = False
    poll_interval_s: float = 5.0
    max_events_per_poll: int = 100
    max_file_size_mb: float = 16.0
    read_only: bool = True
    modality_hint: Optional[str] = None
    trust_level: str = TrustLevel.LOW
    provenance_label: str = ""
    recursive: bool = False
    max_file_count: int = 200
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.source_type not in SensorySourceType.ALL:
            self.source_type = SensorySourceType.UNKNOWN
        # Read-only is an invariant, never configurable to False.
        self.read_only = True
        if not self.provenance_label:
            self.provenance_label = f"{self.source_type}:{self.source_id}"

    @property
    def is_simulated(self) -> bool:
        return self.source_type in SensorySourceType.SIMULATED

    @property
    def is_real_read_only(self) -> bool:
        return self.source_type in SensorySourceType.REAL_READ_ONLY

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__), "is_simulated": self.is_simulated,
                "is_real_read_only": self.is_real_read_only}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SensorySourceConfig":
        valid = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in valid})


@dataclass
class SensorySource:
    """A registered source: its config, live status, and health counters."""

    config: SensorySourceConfig
    status: str = SensorySourceStatus.REGISTERED
    read_only_validated: bool = False
    last_poll_at: Optional[float] = None
    event_count: int = 0
    malformed_count: int = 0
    read_error_count: int = 0
    last_error: str = ""
    registered_at: float = field(default_factory=time.time)

    @property
    def source_id(self) -> str:
        return self.config.source_id

    @property
    def healthy(self) -> bool:
        return self.status in (SensorySourceStatus.REGISTERED,
                               SensorySourceStatus.ACTIVE)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "config": self.config.to_dict(),
            "status": self.status,
            "read_only_validated": self.read_only_validated,
            "last_poll_at": self.last_poll_at,
            "event_count": self.event_count,
            "malformed_count": self.malformed_count,
            "read_error_count": self.read_error_count,
            "last_error": self.last_error,
            "healthy": self.healthy,
        }
