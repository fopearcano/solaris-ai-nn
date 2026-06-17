"""Live observation window -- a bounded summary of one observed event batch.

:class:`LiveObservationWindow` summarizes a bounded batch of accepted live events:
counts, event rates, silence gaps, the dominant source, missing expected sources,
and overload/deprivation markers. Windows are bounded and built from existing event
batches -- there is no infinite tailing -- and absence is recorded, not ignored.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class ObservationWindowStatus:
    OK = "ok"
    OK_WITH_WARNINGS = "ok_with_warnings"
    EMPTY = "empty"
    UNKNOWN = "unknown"

    ALL = (OK, OK_WITH_WARNINGS, EMPTY, UNKNOWN)


def parse_timestamp(ts: str) -> Optional[float]:
    """Parse an ISO-8601 UTC timestamp to epoch seconds (read-only; no clock)."""
    if not ts:
        return None
    raw = str(ts).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(raw)
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


@dataclass
class ObservationWindowSummary:
    """The computed summary metrics for a window."""

    event_count: int = 0
    accepted_event_count: int = 0
    quarantined_event_count: int = 0
    source_count: int = 0
    silence_gap_count: int = 0
    longest_silence_s: float = 0.0
    peak_event_rate_per_min: float = 0.0
    average_event_rate_per_min: float = 0.0
    dominant_source: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class LiveObservationWindow:
    """One bounded observation window over accepted live events."""

    window_id: str
    duration_target_minutes: int = 30
    summary: ObservationWindowSummary = field(
        default_factory=ObservationWindowSummary)
    start_timestamp: str = ""
    end_timestamp: str = ""
    missing_expected_sources: List[str] = field(default_factory=list)
    overload_markers: List[str] = field(default_factory=list)
    deprivation_markers: List[str] = field(default_factory=list)
    safety_findings: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    status: str = ObservationWindowStatus.OK

    def to_dict(self) -> Dict[str, Any]:
        return {
            "window_id": self.window_id,
            "duration_target_minutes": self.duration_target_minutes,
            "start_timestamp": self.start_timestamp,
            "end_timestamp": self.end_timestamp,
            "summary": self.summary.to_dict(),
            "missing_expected_sources": list(self.missing_expected_sources),
            "overload_markers": list(self.overload_markers),
            "deprivation_markers": list(self.deprivation_markers),
            "safety_findings": list(self.safety_findings),
            "limitations": list(self.limitations),
            "status": self.status,
        }


@dataclass
class ObservationWindowBuilder:
    """Builds bounded observation windows from accepted events."""

    silence_gap_threshold_s: float = 600.0  # 10 minutes
    high_rate_per_min: float = 120.0

    def build(self, *, window_id: str, accepted_events: List[Dict[str, Any]],
              quarantined_count: int, expected_sources: List[str],
              duration_target_minutes: int = 30) -> LiveObservationWindow:
        window = LiveObservationWindow(
            window_id=window_id,
            duration_target_minutes=duration_target_minutes)
        s = window.summary
        s.event_count = len(accepted_events) + quarantined_count
        s.accepted_event_count = len(accepted_events)
        s.quarantined_event_count = quarantined_count

        sources: Dict[str, int] = {}
        stamps: List[float] = []
        for ev in accepted_events:
            sources[ev.get("source_id", "")] = \
                sources.get(ev.get("source_id", ""), 0) + 1
            t = parse_timestamp(ev.get("timestamp_utc", ""))
            if t is not None:
                stamps.append(t)
        s.source_count = len(sources)
        if sources:
            s.dominant_source = max(sources, key=sources.get)

        stamps.sort()
        if stamps:
            window.start_timestamp = accepted_events[0].get("timestamp_utc", "")
            window.end_timestamp = accepted_events[-1].get("timestamp_utc", "")
            span_s = max(stamps[-1] - stamps[0], 0.0)
            span_min = span_s / 60.0 if span_s > 0 else 0.0
            s.average_event_rate_per_min = (
                len(stamps) / span_min if span_min > 0 else float(len(stamps)))
            # Silence gaps + peak rate from inter-event deltas.
            peak = s.average_event_rate_per_min
            for prev, nxt in zip(stamps[:-1], stamps[1:]):
                delta = nxt - prev
                if delta >= self.silence_gap_threshold_s:
                    s.silence_gap_count += 1
                    s.longest_silence_s = max(s.longest_silence_s, delta)
                if delta > 0:
                    peak = max(peak, 60.0 / delta)
            s.peak_event_rate_per_min = peak

        # Missing expected sources.
        window.missing_expected_sources = [
            src for src in expected_sources if src not in sources]

        # Overload / deprivation markers (window-level, descriptive).
        if s.peak_event_rate_per_min > self.high_rate_per_min:
            window.overload_markers.append("peak_event_rate_too_high")
        if s.quarantined_event_count > max(1, s.accepted_event_count):
            window.overload_markers.append("quarantine_burst")
        if s.accepted_event_count == 0:
            window.deprivation_markers.append("no_accepted_events")
        if s.source_count == 1 and s.accepted_event_count > 0:
            window.deprivation_markers.append("only_one_source_active")
        if window.missing_expected_sources:
            window.deprivation_markers.append("missing_expected_source")

        if s.accepted_event_count == 0:
            window.status = ObservationWindowStatus.EMPTY
        elif window.overload_markers or window.deprivation_markers:
            window.status = ObservationWindowStatus.OK_WITH_WARNINGS
        else:
            window.status = ObservationWindowStatus.OK
        return window
