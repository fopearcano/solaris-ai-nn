"""Ecology streams -- ecology events become canonical signals.

The stream turns an :class:`EcologyStimulus` into a Solaris-compatible
``C.Stimulus`` the neural bridge already understands (absence events
become ``is_absence=True``), exposes a ``stimulus_provider(step)``
callable for the runner, and can write/replay the event stream as JSONL
for deterministic reproduction.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .events import EcologyEventType, EcologyStimulus, StimulusSource


def to_canonical_signal(stimulus: EcologyStimulus) -> Any:
    """One EcologyStimulus -> one canonical ``C.Stimulus``."""
    from ..signals import canonical as C

    return C.Stimulus(
        origin="developmental_nursery",
        modality=stimulus.modality,
        payload=stimulus.payload,
        intensity=stimulus.intensity,
        is_absence=stimulus.is_absence)


@dataclass
class EcologyStream:
    """Bridges nursery events to canonical signals and JSONL."""

    state_dir: Optional[Union[str, Path]] = None
    write_log: bool = True
    events_written: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self.events_path = (Path(self.state_dir) / "ecology_events.jsonl"
                            if self.state_dir else None)
        self.stream_path = (Path(self.state_dir) / "ecology_stream.jsonl"
                            if self.state_dir else None)

    def to_canonical_signal(self, stimulus: EcologyStimulus) -> Any:
        return to_canonical_signal(stimulus)

    def emit(self, stimulus: EcologyStimulus) -> Any:
        """Convert + (optionally) log; returns the canonical signal."""
        signal = to_canonical_signal(stimulus)
        if self.write_log and self.events_path is not None:
            self._append(self.events_path, stimulus.to_dict())
            self._append(self.stream_path, {
                "step": stimulus.step,
                "modality": signal.modality,
                "payload": signal.payload,
                "intensity": signal.intensity,
                "is_absence": signal.is_absence,
                "event_type": stimulus.event_type})
        self.events_written += 1
        return signal

    def _append(self, path: Optional[Path],
                row: Dict[str, Any]) -> None:
        if path is None:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, default=str) + "\n")

    # -- replay -------------------------------------------------------------------

    def replay_jsonl(self, path: Union[str, Path],
                     ) -> List[EcologyStimulus]:
        """Load a previously written event log into stimuli."""
        stimuli: List[EcologyStimulus] = []
        for line in Path(path).read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            stimuli.append(EcologyStimulus(
                event_type=row["event_type"],
                source=row.get("source",
                               StimulusSource.DEVELOPMENTAL_NURSERY),
                modality=row.get("modality", "generic"),
                payload=row.get("payload"),
                intensity=float(row.get("intensity", 0.0)),
                stimulus_id=row.get("stimulus_id", ""),
                step=int(row.get("step", 0))))
        return stimuli

    def write_jsonl(self, path: Union[str, Path],
                    stimuli: List[EcologyStimulus]) -> str:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            for stimulus in stimuli:
                fh.write(json.dumps(stimulus.to_dict(), default=str)
                         + "\n")
        return str(path)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "events_written": self.events_written,
            "events_path": (str(self.events_path)
                            if self.events_path else None),
            "stream_path": (str(self.stream_path)
                            if self.stream_path else None),
        }
