"""Live rhythm analysis -- descriptive temporal patterns, never overfit.

:class:`LiveRhythmAnalyzer` detects periodic, bursty, and irregular per-source
behaviour from event timestamps. Detection is descriptive: small windows are not
overfit, weak rhythms are marked weak, and no rhythm implies intelligence or life.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .observation_window import parse_timestamp


class RhythmKind:
    PERIODIC = "periodic"
    BURSTY = "bursty"
    IRREGULAR = "irregular"
    SPARSE = "sparse"
    UNKNOWN = "unknown"

    ALL = (PERIODIC, BURSTY, IRREGULAR, SPARSE, UNKNOWN)


class RhythmStrength:
    STRONG = "strong"
    WEAK = "weak"
    NONE = "none"

    ALL = (STRONG, WEAK, NONE)


@dataclass
class RhythmPattern:
    """One per-source rhythm pattern."""

    source_id: str
    kind: str = RhythmKind.UNKNOWN
    strength: str = RhythmStrength.NONE
    event_count: int = 0
    mean_interval_s: float = 0.0
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"source_id": self.source_id, "kind": self.kind,
                "strength": self.strength, "event_count": self.event_count,
                "mean_interval_s": round(self.mean_interval_s, 2),
                "detail": self.detail, "implies_intelligence": False}


@dataclass
class RhythmFinding:
    finding: str
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"finding": self.finding, "detail": self.detail}


@dataclass
class LiveRhythmAnalysis:
    """The aggregate rhythm analysis."""

    patterns: List[RhythmPattern] = field(default_factory=list)
    findings: List[RhythmFinding] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rhythm_pattern_count": len(self.patterns),
            "periodic_source_count": sum(1 for p in self.patterns
                                         if p.kind == RhythmKind.PERIODIC),
            "bursty_source_count": sum(1 for p in self.patterns
                                       if p.kind == RhythmKind.BURSTY),
            "patterns": [p.to_dict() for p in self.patterns],
            "findings": [f.to_dict() for f in self.findings],
            "note": "rhythm detection is descriptive; weak rhythms are marked "
                    "weak and no rhythm implies intelligence or life",
        }


@dataclass
class LiveRhythmAnalyzer:
    """Detects per-source rhythm from event timestamps (no overfitting)."""

    min_events_for_rhythm: int = 4
    periodic_cv_threshold: float = 0.35  # coefficient of variation

    def analyze(self, accepted_events: List[Dict[str, Any]]) -> LiveRhythmAnalysis:
        analysis = LiveRhythmAnalysis()
        by_source: Dict[str, List[float]] = {}
        for ev in accepted_events:
            t = parse_timestamp(ev.get("timestamp_utc", ""))
            if t is not None:
                by_source.setdefault(ev.get("source_id", ""), []).append(t)
        for source_id, stamps in by_source.items():
            analysis.patterns.append(self._pattern(source_id, sorted(stamps)))
        if not analysis.patterns:
            analysis.findings.append(RhythmFinding(
                "no_rhythm", "insufficient timestamped events for rhythm"))
        return analysis

    def _pattern(self, source_id: str, stamps: List[float]) -> RhythmPattern:
        p = RhythmPattern(source_id=source_id, event_count=len(stamps))
        if len(stamps) < 2:
            p.kind = RhythmKind.SPARSE
            p.detail = "too few events to characterize rhythm"
            return p
        intervals = [b - a for a, b in zip(stamps[:-1], stamps[1:])]
        p.mean_interval_s = statistics.mean(intervals) if intervals else 0.0
        if len(stamps) < self.min_events_for_rhythm:
            p.kind = RhythmKind.SPARSE
            p.strength = RhythmStrength.WEAK
            p.detail = "small window; rhythm marked weak (not overfit)"
            return p
        mean = p.mean_interval_s
        stdev = statistics.pstdev(intervals) if len(intervals) > 1 else 0.0
        cv = (stdev / mean) if mean > 0 else float("inf")
        if cv <= self.periodic_cv_threshold:
            p.kind = RhythmKind.PERIODIC
            p.strength = (RhythmStrength.STRONG
                          if len(stamps) >= 6 else RhythmStrength.WEAK)
            p.detail = f"regular interval ~{mean:.0f}s (cv={cv:.2f})"
        elif cv >= 1.5:
            p.kind = RhythmKind.BURSTY
            p.strength = RhythmStrength.WEAK if len(stamps) < 6 \
                else RhythmStrength.STRONG
            p.detail = f"bursty arrival (cv={cv:.2f})"
        else:
            p.kind = RhythmKind.IRREGULAR
            p.strength = RhythmStrength.WEAK
            p.detail = f"irregular arrival (cv={cv:.2f})"
        return p
