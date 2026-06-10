"""Stream sensors -- turn ingested events into canonical Stimuli.

Each sensor is a callable ``(step) -> Optional[Stimulus]`` so it plugs
directly into ``ContinuousRunner(stimulus_provider=sensor)``. Sensors never
read anything the ingestor did not validate, and never act on the world.

``SilenceWindowSensor`` mirrors Solaris_Ai's absence-stimulus idea at the
stream level: when the wrapped source pauses longer than the configured
window, the *absence itself* becomes a Stimulus (Subtraction Principle).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from ..signals import canonical as C
from .stream_ingestion import ReadOnlyStreamIngestor


def event_to_stimulus(event: Dict[str, Any]) -> C.Stimulus:
    """One normalized stream event -> one canonical Stimulus."""
    return C.Stimulus(
        origin=str(event.get("source", "stream")),
        modality=str(event.get("modality", "generic")),
        payload=event.get("payload"),
        intensity=float(event.get("intensity", 0.5)),
        is_absence=False,
    )


@dataclass
class _FileStreamSensor:
    """Shared machinery: read a file once, emit one Stimulus per call."""

    path: Union[str, Path]
    fmt: str = "jsonl"
    default_intensity: float = 0.5
    ingestor: Optional[ReadOnlyStreamIngestor] = None

    _events: Optional[List[Dict[str, Any]]] = field(default=None, init=False)
    _index: int = field(default=0, init=False)
    emitted: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        if self.ingestor is None:
            self.ingestor = ReadOnlyStreamIngestor(
                default_intensity=self.default_intensity)

    def _load(self) -> List[Dict[str, Any]]:
        if self._events is None:
            self._events = self.ingestor.read_once(self.path, fmt=self.fmt)
        return self._events

    @property
    def exhausted(self) -> bool:
        return self._events is not None and self._index >= len(self._events)

    def next_stimulus(self, step: int) -> Optional[C.Stimulus]:
        events = self._load()
        if self._index >= len(events):
            return None
        event = events[self._index]
        self._index += 1
        self.emitted += 1
        return event_to_stimulus(event)

    __call__ = next_stimulus

    def snapshot(self) -> Dict[str, Any]:
        return {
            "sensor": type(self).__name__,
            "path": str(self.path),
            "format": self.fmt,
            "events_available": len(self._events or []),
            "emitted": self.emitted,
            "exhausted": self.exhausted,
            "ingestion": self.ingestor.snapshot(),
        }


@dataclass
class JsonlStreamSensor(_FileStreamSensor):
    """Emits Stimuli from a JSONL sensory-event file."""

    fmt: str = "jsonl"


@dataclass
class TextStreamSensor(_FileStreamSensor):
    """Emits text-modality Stimuli, one per line of a plain text file."""

    fmt: str = "text"


@dataclass
class SyntheticHeartbeatSensor:
    """Emits a low-intensity internal heartbeat Stimulus every N steps.

    Useful as a deterministic background source in pilots with sparse
    streams; fully internal, never reads anything.
    """

    interval_steps: int = 10
    intensity: float = 0.1
    emitted: int = field(default=0, init=False)

    def next_stimulus(self, step: int) -> Optional[C.Stimulus]:
        if self.interval_steps <= 0 or step % self.interval_steps != 0:
            return None
        self.emitted += 1
        return C.Stimulus(origin="pilot_heartbeat", modality="internal",
                          payload="heartbeat", intensity=self.intensity)

    __call__ = next_stimulus

    def snapshot(self) -> Dict[str, Any]:
        return {"sensor": "SyntheticHeartbeatSensor",
                "interval_steps": self.interval_steps,
                "emitted": self.emitted}


@dataclass
class SilenceWindowSensor:
    """Wraps a source sensor; emits absence Stimuli when the stream pauses.

    When ``source`` yields nothing for ``window_steps`` consecutive calls,
    each further silent call emits an ``is_absence=True`` Stimulus whose
    intensity escalates gently (capped at ``max_intensity``).
    """

    source: Callable[[int], Optional[C.Stimulus]]
    window_steps: int = 5
    escalation: float = 0.1
    max_intensity: float = 1.0
    origin: str = "silence_window"

    _silence: int = field(default=0, init=False)
    _intensity: float = field(default=0.0, init=False)
    absences_emitted: int = field(default=0, init=False)

    def next_stimulus(self, step: int) -> Optional[C.Stimulus]:
        stimulus = self.source(step)
        if stimulus is not None:
            self._silence = 0
            self._intensity = 0.0
            return stimulus
        self._silence += 1
        if self._silence < self.window_steps:
            return None
        self._intensity = min(self.max_intensity,
                              self._intensity + self.escalation)
        self.absences_emitted += 1
        return C.Stimulus(origin=self.origin, modality="internal",
                          payload="stream silence", is_absence=True,
                          intensity=self._intensity)

    __call__ = next_stimulus

    def snapshot(self) -> Dict[str, Any]:
        inner = (self.source.snapshot()
                 if hasattr(self.source, "snapshot") else None)
        return {"sensor": "SilenceWindowSensor",
                "window_steps": self.window_steps,
                "current_silence": self._silence,
                "absences_emitted": self.absences_emitted,
                "source": inner}


def build_stream_sensor(path: Union[str, Path], fmt: Optional[str] = None,
                        silence_window: int = 5,
                        default_intensity: float = 0.5) -> SilenceWindowSensor:
    """The standard pilot wiring: file sensor wrapped in a silence window."""
    fmt = fmt or ReadOnlyStreamIngestor.detect_format(path)
    sensor_cls = JsonlStreamSensor if fmt == "jsonl" else TextStreamSensor
    inner = sensor_cls(path=path, default_intensity=default_intensity)
    return SilenceWindowSensor(source=inner, window_steps=silence_window)
