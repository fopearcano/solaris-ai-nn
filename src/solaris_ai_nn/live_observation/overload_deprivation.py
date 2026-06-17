"""Live overload / deprivation assessment -- too much or too little stimulus.

:class:`LiveOverloadDeprivationAssessor` combines window, source-health, source-diet,
rhythm, and absence signals into a single load assessment: is the field overloaded
(too many events, quarantine bursts, peak-rate spikes) or deprived (no events, a
single source, missing expected sources, persistent global silence)? Severe overload
or severe deprivation blocks any later ontogenesis recommendation; a mixed picture
requires operator review. No feeder is ever started, stopped, or reconfigured -- the
assessment is observational and report-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class LoadStatus:
    STABLE = "stable"
    MILD_OVERLOAD = "mild_overload"
    SEVERE_OVERLOAD = "severe_overload"
    MILD_DEPRIVATION = "mild_deprivation"
    SEVERE_DEPRIVATION = "severe_deprivation"
    MIXED = "mixed"
    UNKNOWN = "unknown"

    ALL = (STABLE, MILD_OVERLOAD, SEVERE_OVERLOAD, MILD_DEPRIVATION,
           SEVERE_DEPRIVATION, MIXED, UNKNOWN)


@dataclass
class OverloadMarker:
    """One overload marker (descriptive; never a feeder action)."""

    marker: str
    severe: bool = False
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"marker": self.marker, "severe": self.severe,
                "detail": self.detail, "triggers_feeder_change": False}


@dataclass
class DeprivationMarker:
    """One deprivation marker (descriptive; never a feeder action)."""

    marker: str
    severe: bool = False
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"marker": self.marker, "severe": self.severe,
                "detail": self.detail, "triggers_feeder_change": False}


@dataclass
class LiveOverloadDeprivationAssessment:
    """The combined overload / deprivation assessment."""

    status: str = LoadStatus.UNKNOWN
    overload_markers: List[OverloadMarker] = field(default_factory=list)
    deprivation_markers: List[DeprivationMarker] = field(default_factory=list)
    requires_operator_review: bool = False
    notes: List[str] = field(default_factory=list)

    @property
    def severe_overload(self) -> bool:
        return self.status == LoadStatus.SEVERE_OVERLOAD or any(
            m.severe for m in self.overload_markers)

    @property
    def severe_deprivation(self) -> bool:
        return self.status == LoadStatus.SEVERE_DEPRIVATION or any(
            m.severe for m in self.deprivation_markers)

    @property
    def blocks_ontogenesis(self) -> bool:
        """Severe overload or severe deprivation blocks ontogenesis."""
        return self.severe_overload or self.severe_deprivation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "load_status": self.status,
            "overload_marker_count": len(self.overload_markers),
            "deprivation_marker_count": len(self.deprivation_markers),
            "overload_markers": [m.to_dict() for m in self.overload_markers],
            "deprivation_markers": [m.to_dict()
                                    for m in self.deprivation_markers],
            "severe_overload": self.severe_overload,
            "severe_deprivation": self.severe_deprivation,
            "blocks_ontogenesis_recommendation": self.blocks_ontogenesis,
            "requires_operator_review": self.requires_operator_review,
            "notes": list(self.notes),
            "note": "severe overload or deprivation blocks any later ontogenesis "
                    "recommendation; a mixed picture requires operator review; no "
                    "feeder is started, stopped, or reconfigured",
        }


@dataclass
class LiveOverloadDeprivationAssessor:
    """Builds the load assessment from upstream observation signals."""

    high_rate_per_min: float = 120.0
    severe_rate_per_min: float = 300.0

    def assess(self, *, windows: List[Dict[str, Any]],
               source_health_summary: Dict[str, Any],
               source_diet: Dict[str, Any],
               absence: Dict[str, Any]) -> LiveOverloadDeprivationAssessment:
        a = LiveOverloadDeprivationAssessment()

        accepted_total = sum(int((w.get("summary") or {})
                                 .get("accepted_event_count", 0))
                             for w in windows)
        peak_rate = max((float((w.get("summary") or {})
                               .get("peak_event_rate_per_min", 0.0))
                         for w in windows), default=0.0)
        quarantine_burst = any("quarantine_burst" in (w.get("overload_markers")
                                                      or []) for w in windows)
        rate_too_high = any("peak_event_rate_too_high"
                            in (w.get("overload_markers") or [])
                            for w in windows)

        # -- Overload markers --------------------------------------------------
        if peak_rate >= self.severe_rate_per_min:
            a.overload_markers.append(OverloadMarker(
                "peak_event_rate_severe", severe=True,
                detail=f"peak ~{peak_rate:.0f}/min exceeds severe bound"))
        elif rate_too_high or peak_rate >= self.high_rate_per_min:
            a.overload_markers.append(OverloadMarker(
                "peak_event_rate_high",
                detail=f"peak ~{peak_rate:.0f}/min above comfortable bound"))
        if quarantine_burst:
            a.overload_markers.append(OverloadMarker(
                "quarantine_burst",
                detail="quarantined events outnumber accepted in a window"))

        # -- Deprivation markers ----------------------------------------------
        deprivation_windows = int(absence.get("deprivation_window_count", 0))
        global_silence = accepted_total == 0
        single_source = int(source_diet.get("total_events", 0)) > 0 and \
            source_diet.get("balance") == "single_source"
        silent_sources = int(source_health_summary.get(
            "live_silent_source_count", 0))
        live_sources = int(source_health_summary.get("live_source_count", 0))

        if global_silence:
            a.deprivation_markers.append(DeprivationMarker(
                "global_silence", severe=True,
                detail="no accepted events observed across all windows"))
        if single_source and not global_silence:
            a.deprivation_markers.append(DeprivationMarker(
                "single_source_only",
                detail="all events came from a single source"))
        if deprivation_windows >= 2:
            a.deprivation_markers.append(DeprivationMarker(
                "repeated_deprivation_windows", severe=deprivation_windows >= 3,
                detail=f"{deprivation_windows} deprivation window(s) recorded"))
        elif deprivation_windows == 1:
            a.deprivation_markers.append(DeprivationMarker(
                "deprivation_window",
                detail="one deprivation window recorded"))
        if live_sources and silent_sources >= max(1, live_sources - 1) \
                and not global_silence:
            a.deprivation_markers.append(DeprivationMarker(
                "most_sources_silent",
                detail=f"{silent_sources}/{live_sources} sources silent"))

        a.status = self._status(a)
        a.requires_operator_review = a.status == LoadStatus.MIXED
        if a.status == LoadStatus.UNKNOWN:
            a.notes.append("insufficient signal to assess load")
        return a

    @staticmethod
    def _status(a: LiveOverloadDeprivationAssessment) -> str:
        has_over = bool(a.overload_markers)
        has_dep = bool(a.deprivation_markers)
        severe_over = any(m.severe for m in a.overload_markers)
        severe_dep = any(m.severe for m in a.deprivation_markers)
        if has_over and has_dep:
            return LoadStatus.MIXED
        if severe_over:
            return LoadStatus.SEVERE_OVERLOAD
        if severe_dep:
            return LoadStatus.SEVERE_DEPRIVATION
        if has_over:
            return LoadStatus.MILD_OVERLOAD
        if has_dep:
            return LoadStatus.MILD_DEPRIVATION
        return LoadStatus.STABLE
