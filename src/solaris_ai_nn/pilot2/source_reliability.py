"""Pilot-2 source reliability -- track per-source health and usefulness.

The :class:`SourceReliabilityMonitor` accumulates per-source counters (reads,
malformed, missing, duplicates, bursts, provenance) and classifies each source
as reliable / noisy-but-useful / unstable / malformed / unsafe / unknown.
Unsafe sources must be disabled; noisy-but-useful sources may remain if
bounded. Reliability feeds source curation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ReliabilityClass:
    RELIABLE = "reliable"
    NOISY_BUT_USEFUL = "noisy_but_useful"
    UNSTABLE = "unstable"
    MALFORMED = "malformed"
    UNSAFE = "unsafe"
    UNKNOWN = "unknown"

    ALL = (RELIABLE, NOISY_BUT_USEFUL, UNSTABLE, MALFORMED, UNSAFE, UNKNOWN)


@dataclass
class SourceReliabilityRecord:
    """Accumulated reliability signals for one source."""

    source_id: str
    polls: int = 0
    successful_polls: int = 0
    total_events: int = 0
    malformed_events: int = 0
    missing_events: int = 0
    duplicate_events: int = 0
    burst_events: int = 0
    provenance_present: int = 0
    drift: float = 0.0
    noise_level: float = 0.0
    usefulness: float = 0.0
    safety_warnings: int = 0
    unsafe: bool = False
    last_update: float = field(default_factory=time.time)

    @property
    def uptime(self) -> float:
        return round(self.successful_polls / self.polls, 4) if self.polls \
            else 1.0

    @property
    def read_success_rate(self) -> float:
        return self.uptime

    @property
    def malformed_rate(self) -> float:
        return round(self.malformed_events / self.total_events, 4) \
            if self.total_events else 0.0

    @property
    def duplicate_rate(self) -> float:
        return round(self.duplicate_events / self.total_events, 4) \
            if self.total_events else 0.0

    @property
    def provenance_completeness(self) -> float:
        return round(self.provenance_present / self.total_events, 4) \
            if self.total_events else 1.0

    def classify(self) -> str:
        if self.unsafe or self.safety_warnings >= 3:
            return ReliabilityClass.UNSAFE
        if self.polls == 0 or self.total_events == 0:
            return ReliabilityClass.UNKNOWN
        if self.malformed_rate > 0.5:
            return ReliabilityClass.MALFORMED
        if self.uptime < 0.5 or self.drift > 0.7:
            return ReliabilityClass.UNSTABLE
        if self.noise_level > 0.4 and self.usefulness > 0.3:
            return ReliabilityClass.NOISY_BUT_USEFUL
        if self.uptime >= 0.8 and self.malformed_rate < 0.1:
            return ReliabilityClass.RELIABLE
        return ReliabilityClass.UNKNOWN

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "uptime": self.uptime,
            "read_success_rate": self.read_success_rate,
            "malformed_rate": self.malformed_rate,
            "duplicate_rate": self.duplicate_rate,
            "provenance_completeness": self.provenance_completeness,
            "drift": self.drift,
            "noise_level": self.noise_level,
            "usefulness": self.usefulness,
            "safety_warnings": self.safety_warnings,
            "reliability_class": self.classify(),
            "must_disable": self.classify() == ReliabilityClass.UNSAFE,
        }


@dataclass
class SourceReliabilityMonitor:
    """Tracks and classifies per-source reliability."""

    records: Dict[str, SourceReliabilityRecord] = field(default_factory=dict)

    def record(self, source_id: str) -> SourceReliabilityRecord:
        return self.records.setdefault(source_id,
                                       SourceReliabilityRecord(source_id))

    def observe_poll(self, source_id: str, *, success: bool, events: int = 0,
                     malformed: int = 0, duplicates: int = 0,
                     missing: int = 0, provenance: int = 0,
                     noise: float = 0.0, usefulness: float = 0.0,
                     unsafe: bool = False) -> SourceReliabilityRecord:
        rec = self.record(source_id)
        rec.polls += 1
        rec.successful_polls += int(success)
        rec.total_events += events
        rec.malformed_events += malformed
        rec.duplicate_events += duplicates
        rec.missing_events += missing
        rec.provenance_present += provenance
        rec.noise_level = round(0.7 * rec.noise_level + 0.3 * noise, 4)
        rec.usefulness = round(max(rec.usefulness, usefulness), 4)
        if unsafe:
            rec.unsafe = True
            rec.safety_warnings += 1
        rec.last_update = time.time()
        return rec

    def unsafe_sources(self) -> List[str]:
        return sorted(sid for sid, r in self.records.items()
                      if r.classify() == ReliabilityClass.UNSAFE)

    def reliable_sources(self) -> List[str]:
        return sorted(sid for sid, r in self.records.items()
                      if r.classify() == ReliabilityClass.RELIABLE)

    def by_class(self) -> Dict[str, int]:
        out: Dict[str, int] = {c: 0 for c in ReliabilityClass.ALL}
        for r in self.records.values():
            out[r.classify()] += 1
        return out

    def curation_feedback(self) -> Dict[str, Any]:
        """Feedback the source curator can act on."""
        return {"disable": self.unsafe_sources(),
                "keep": self.reliable_sources(),
                "by_class": self.by_class()}

    def snapshot(self) -> Dict[str, Any]:
        return {
            "source_count": len(self.records),
            "by_class": self.by_class(),
            "unsafe": self.unsafe_sources(),
            "reliable": self.reliable_sources(),
            "records": {sid: r.to_dict() for sid, r in self.records.items()},
        }
