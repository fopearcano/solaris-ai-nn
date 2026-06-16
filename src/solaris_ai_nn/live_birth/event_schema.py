"""Live sensory event schema -- the read-only event envelope.

:class:`LiveSensoryEvent` is one read-only environmental event from an external
feeder. ``read_only`` must be true, ``is_command`` must be false,
``human_label_is_ground_truth`` and ``debug_gloss_is_ground_truth`` must be false;
secrets/instructions/private data trigger quarantine. Sensory text is never a
command and labels/gloss are never ground truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


class LiveEventSource:
    CHRONOS_ABSENCE = "chronos_absence"
    MACHINE_BODY = "machine_body"
    LOCAL_ENVIRONMENT_MANUAL = "local_environment_manual"
    LOCAL_WEATHER = "local_weather_readonly_external"
    PROJECT_ARTIFACT_FIELD = "project_artifact_field"
    OPERATOR_PULSE = "operator_pulse"


@dataclass
class LiveEventQuality:
    """Bounded quality descriptors for an event."""

    completeness: float = 1.0
    noise: float = 0.0
    is_absence: bool = False
    is_noisy: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"completeness": self.completeness, "noise": self.noise,
                "is_absence": self.is_absence, "is_noisy": self.is_noisy}

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> "LiveEventQuality":
        d = d or {}
        return cls(completeness=float(d.get("completeness", 1.0) or 0.0),
                   noise=float(d.get("noise", 0.0) or 0.0),
                   is_absence=bool(d.get("is_absence", False)),
                   is_noisy=bool(d.get("is_noisy", False)))


@dataclass
class LiveEventSafety:
    """Required safety flags for an event."""

    private_data: bool = False
    contains_instruction: bool = False
    contains_secret: bool = False
    allow_learning: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"private_data": self.private_data,
                "contains_instruction": self.contains_instruction,
                "contains_secret": self.contains_secret,
                "allow_learning": self.allow_learning}

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> "LiveEventSafety":
        d = d or {}
        return cls(private_data=bool(d.get("private_data", False)),
                   contains_instruction=bool(d.get("contains_instruction",
                                                   False)),
                   contains_secret=bool(d.get("contains_secret", False)),
                   allow_learning=bool(d.get("allow_learning", False)))


@dataclass
class LiveSensoryEvent:
    """One read-only environmental sensory event."""

    event_id: str
    timestamp_utc: str
    source_id: str
    modality: str
    channel: str
    read_only: bool = True
    is_command: bool = False
    human_label_is_ground_truth: bool = False
    payload: Any = None
    quality: LiveEventQuality = field(default_factory=LiveEventQuality)
    safety: LiveEventSafety = field(default_factory=LiveEventSafety)
    debug_gloss: str = ""
    debug_gloss_is_ground_truth: bool = False
    sequence_id: str = ""
    source_clock: str = ""
    privacy_notes: str = ""
    limitations: str = ""

    @property
    def well_formed_flags(self) -> bool:
        return (self.read_only is True
                and self.is_command is False
                and self.human_label_is_ground_truth is False
                and self.debug_gloss_is_ground_truth is False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id, "timestamp_utc": self.timestamp_utc,
            "source_id": self.source_id, "modality": self.modality,
            "channel": self.channel, "read_only": self.read_only,
            "is_command": self.is_command,
            "human_label_is_ground_truth": self.human_label_is_ground_truth,
            "payload": self.payload, "quality": self.quality.to_dict(),
            "safety": self.safety.to_dict(), "debug_gloss": self.debug_gloss,
            "debug_gloss_is_ground_truth": self.debug_gloss_is_ground_truth,
            "sequence_id": self.sequence_id, "source_clock": self.source_clock,
            "privacy_notes": self.privacy_notes, "limitations": self.limitations,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LiveSensoryEvent":
        return cls(
            event_id=str(d.get("event_id", "")),
            timestamp_utc=str(d.get("timestamp_utc", "")),
            source_id=str(d.get("source_id", "")),
            modality=str(d.get("modality", "")),
            channel=str(d.get("channel", "")),
            read_only=bool(d.get("read_only", False)),
            is_command=bool(d.get("is_command", False)),
            human_label_is_ground_truth=bool(
                d.get("human_label_is_ground_truth", False)),
            payload=d.get("payload"),
            quality=LiveEventQuality.from_dict(d.get("quality")),
            safety=LiveEventSafety.from_dict(d.get("safety")),
            debug_gloss=str(d.get("debug_gloss", "")),
            debug_gloss_is_ground_truth=bool(
                d.get("debug_gloss_is_ground_truth", False)),
            sequence_id=str(d.get("sequence_id", "")),
            source_clock=str(d.get("source_clock", "")),
            privacy_notes=str(d.get("privacy_notes", "")),
            limitations=str(d.get("limitations", "")))


@dataclass
class LiveEventEnvelope:
    """The parsed event plus its raw form and source file (for quarantine)."""

    raw: Dict[str, Any]
    source_file: str = ""
    line_number: int = 0
    event: Optional[LiveSensoryEvent] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"source_file": self.source_file, "line_number": self.line_number,
                "raw": self.raw,
                "event": self.event.to_dict() if self.event else None}


REQUIRED_FIELDS = ("event_id", "timestamp_utc", "source_id", "modality",
                   "channel", "read_only", "is_command",
                   "human_label_is_ground_truth", "payload", "quality", "safety")
REQUIRED_SAFETY_FIELDS = ("private_data", "contains_instruction",
                          "contains_secret", "allow_learning")
