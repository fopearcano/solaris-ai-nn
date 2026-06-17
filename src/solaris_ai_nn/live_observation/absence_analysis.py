"""Live absence analysis -- absence is a valid environmental signal.

:class:`LiveAbsenceAnalyzer` records no-event windows, source-specific silence,
missing expected sources, and absence-as-deprivation vs absence-as-stable-background
markers. Absence is a valid environmental signal; it must not be confused with
system death, must not be anthropomorphized, and findings are observational only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .observation_window import parse_timestamp


class AbsenceKind:
    GLOBAL_SILENCE = "global_silence"
    SOURCE_SILENCE = "source_silence"
    MISSING_EXPECTED_SOURCE = "missing_expected_source"
    SILENCE_AFTER_BURST = "silence_after_burst"
    REPEATED_ABSENCE = "repeated_absence_pattern"
    STABLE_BACKGROUND = "stable_background"

    ALL = (GLOBAL_SILENCE, SOURCE_SILENCE, MISSING_EXPECTED_SOURCE,
           SILENCE_AFTER_BURST, REPEATED_ABSENCE, STABLE_BACKGROUND)


@dataclass
class AbsenceWindow:
    """One detected absence window."""

    kind: str
    source_id: str = ""
    duration_s: float = 0.0
    is_deprivation: bool = False
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"kind": self.kind, "source_id": self.source_id,
                "duration_s": round(self.duration_s, 1),
                "is_deprivation": self.is_deprivation, "detail": self.detail,
                "is_system_death": False, "anthropomorphized": False}


@dataclass
class AbsenceFinding:
    finding: str
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"finding": self.finding, "detail": self.detail}


@dataclass
class LiveAbsenceAnalysis:
    """The aggregate absence analysis."""

    windows: List[AbsenceWindow] = field(default_factory=list)
    findings: List[AbsenceFinding] = field(default_factory=list)

    @property
    def absence_window_count(self) -> int:
        return len(self.windows)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "live_absence_window_count": self.absence_window_count,
            "deprivation_window_count": sum(1 for w in self.windows
                                            if w.is_deprivation),
            "windows": [w.to_dict() for w in self.windows],
            "findings": [f.to_dict() for f in self.findings],
            "note": "absence is a valid environmental signal; it is not system "
                    "death and is not anthropomorphized; findings are "
                    "observational only",
        }


@dataclass
class LiveAbsenceAnalyzer:
    """Detects absence windows from accepted events + expected sources."""

    silence_gap_threshold_s: float = 600.0

    def analyze(self, *, accepted_events: List[Dict[str, Any]],
                expected_sources: List[str]) -> LiveAbsenceAnalysis:
        analysis = LiveAbsenceAnalysis()
        observed = {ev.get("source_id", "") for ev in accepted_events}

        # Global silence (no events at all).
        if not accepted_events:
            analysis.windows.append(AbsenceWindow(
                kind=AbsenceKind.GLOBAL_SILENCE, is_deprivation=True,
                detail="no accepted events observed"))
            return analysis

        # Explicit absence-marked events => stable background signal.
        absence_events = [ev for ev in accepted_events
                          if (ev.get("quality", {}) or {}).get("is_absence")]
        if absence_events:
            analysis.windows.append(AbsenceWindow(
                kind=AbsenceKind.STABLE_BACKGROUND, is_deprivation=False,
                detail=f"{len(absence_events)} explicit absence/silence "
                "event(s) -- a stable background signal"))

        # Missing expected sources.
        for src in expected_sources:
            if src not in observed:
                analysis.windows.append(AbsenceWindow(
                    kind=AbsenceKind.MISSING_EXPECTED_SOURCE, source_id=src,
                    is_deprivation=True,
                    detail=f"expected source {src!r} produced no events"))

        # Long global silence gaps from timestamps.
        stamps = sorted(t for t in (parse_timestamp(ev.get("timestamp_utc", ""))
                                    for ev in accepted_events) if t is not None)
        for prev, nxt in zip(stamps[:-1], stamps[1:]):
            delta = nxt - prev
            if delta >= self.silence_gap_threshold_s:
                analysis.windows.append(AbsenceWindow(
                    kind=AbsenceKind.GLOBAL_SILENCE, duration_s=delta,
                    is_deprivation=False,
                    detail="silence gap between events (background)"))

        if not analysis.windows:
            analysis.findings.append(AbsenceFinding(
                "no_absence", "no absence windows detected in this batch"))
        return analysis
