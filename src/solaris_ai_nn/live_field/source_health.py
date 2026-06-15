"""Source health -- watching the feeders the way an organism watches its senses.

A :class:`SourceHealthMonitor` tracks each source's liveness: active, silent,
noisy, flatlined, bursty, delayed, corrupt, unreliable, resumed, a missed rhythm,
or a missing file. Source silence becomes a perceptual absence; source corruption
becomes a safety/evidence issue. Source failure is never hidden.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class SourceHealthState:
    ACTIVE = "active"
    SILENT = "silent"
    NOISY = "noisy"
    FLATLINED = "flatlined"
    BURSTY = "bursty"
    DELAYED = "delayed"
    CORRUPT = "corrupt"
    UNRELIABLE = "unreliable"
    RESUMED = "resumed"
    UNKNOWN = "unknown"

    ALL = (ACTIVE, SILENT, NOISY, FLATLINED, BURSTY, DELAYED, CORRUPT,
           UNRELIABLE, RESUMED, UNKNOWN)


class SourceHealthEventType:
    STATE_CHANGED = "state_changed"
    EXPECTED_RHYTHM_MISSED = "expected_rhythm_missed"
    EXPECTED_FILE_MISSING = "expected_file_missing"
    CORRUPT_RECORD = "corrupt_record"

    ALL = (STATE_CHANGED, EXPECTED_RHYTHM_MISSED, EXPECTED_FILE_MISSING,
           CORRUPT_RECORD)


@dataclass
class SourceHealthEvent:
    event_type: str
    source_id: str
    old_state: Optional[str] = None
    new_state: Optional[str] = None
    detail: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class _SourceRecord:
    source_id: str
    state: str = SourceHealthState.UNKNOWN
    last_seen: float = 0.0
    event_count: int = 0
    corrupt_count: int = 0
    expected_silence_window_s: float = 30.0
    expected_rate: float = 0.0
    recent_intervals: List[float] = field(default_factory=list)


@dataclass
class SourceHealthMonitor:
    """Tracks per-source liveness and emits health events."""

    sources: Dict[str, _SourceRecord] = field(default_factory=dict)
    events: List[SourceHealthEvent] = field(default_factory=list, init=False)

    def register(self, source_id: str, *, expected_silence_window_s: float = 30.0,
                 expected_rate: float = 0.0) -> None:
        self.sources.setdefault(source_id, _SourceRecord(
            source_id=source_id,
            expected_silence_window_s=expected_silence_window_s,
            expected_rate=expected_rate))

    def observe_event(self, source_id: str, timestamp: float, *,
                      corrupt: bool = False) -> None:
        rec = self.sources.get(source_id)
        if rec is None:
            rec = _SourceRecord(source_id=source_id)
            self.sources[source_id] = rec
        if corrupt:
            rec.corrupt_count += 1
            self._emit(SourceHealthEventType.CORRUPT_RECORD, rec,
                       SourceHealthState.CORRUPT, "corrupt record observed")
            self._set_state(rec, SourceHealthState.CORRUPT)
            return
        if rec.last_seen and timestamp > rec.last_seen:
            interval = timestamp - rec.last_seen
            rec.recent_intervals.append(interval)
            rec.recent_intervals = rec.recent_intervals[-20:]
        rec.last_seen = timestamp
        rec.event_count += 1
        was_silent = rec.state in (SourceHealthState.SILENT,
                                   SourceHealthState.FLATLINED,
                                   SourceHealthState.UNKNOWN)
        new_state = self._classify(rec)
        if was_silent and new_state == SourceHealthState.ACTIVE \
                and rec.event_count > 1:
            self._set_state(rec, SourceHealthState.RESUMED)
        else:
            self._set_state(rec, new_state)

    def check_silence(self, now: float) -> List[SourceHealthEvent]:
        """Emit silence/flatline events for overdue sources."""
        out: List[SourceHealthEvent] = []
        for rec in self.sources.values():
            if rec.event_count == 0:
                continue
            elapsed = now - rec.last_seen
            if elapsed > rec.expected_silence_window_s \
                    and rec.state != SourceHealthState.SILENT:
                ev = self._emit(SourceHealthEventType.STATE_CHANGED, rec,
                                SourceHealthState.SILENT,
                                f"silent for {elapsed:.1f}s")
                self._set_state(rec, SourceHealthState.SILENT)
                out.append(ev)
        return out

    def report_missing_file(self, source_id: str, path: str) -> SourceHealthEvent:
        rec = self.sources.setdefault(source_id, _SourceRecord(source_id))
        ev = self._emit(SourceHealthEventType.EXPECTED_FILE_MISSING, rec,
                        SourceHealthState.SILENT,
                        f"expected file missing: {path}")
        rec.state = SourceHealthState.SILENT
        return ev

    def _classify(self, rec: _SourceRecord) -> str:
        intervals = rec.recent_intervals
        if len(intervals) >= 3:
            mean = sum(intervals) / len(intervals)
            if mean < 1e-6:
                return SourceHealthState.BURSTY
        return SourceHealthState.ACTIVE

    def _set_state(self, rec: _SourceRecord, state: str) -> None:
        if rec.state != state:
            self._emit(SourceHealthEventType.STATE_CHANGED, rec, state,
                       f"{rec.state} -> {state}")
        rec.state = state

    def _emit(self, event_type: str, rec: _SourceRecord, new_state: str,
              detail: str) -> SourceHealthEvent:
        ev = SourceHealthEvent(event_type=event_type, source_id=rec.source_id,
                               old_state=rec.state, new_state=new_state,
                               detail=detail)
        self.events.append(ev)
        return ev

    def state_of(self, source_id: str) -> str:
        rec = self.sources.get(source_id)
        return rec.state if rec else SourceHealthState.UNKNOWN

    def silent_sources(self) -> List[str]:
        return [s for s, r in self.sources.items()
                if r.state in (SourceHealthState.SILENT,
                               SourceHealthState.FLATLINED)]

    def corrupt_sources(self) -> List[str]:
        return [s for s, r in self.sources.items() if r.corrupt_count > 0]

    def active_sources(self) -> List[str]:
        return [s for s, r in self.sources.items()
                if r.state in (SourceHealthState.ACTIVE,
                               SourceHealthState.RESUMED,
                               SourceHealthState.BURSTY)]

    def snapshot(self) -> Dict[str, Any]:
        return {
            "source_count": len(self.sources),
            "active_count": len(self.active_sources()),
            "silent_count": len(self.silent_sources()),
            "corrupt_count": len(self.corrupt_sources()),
            "states": {s: r.state for s, r in self.sources.items()},
            "event_count": len(self.events),
        }
