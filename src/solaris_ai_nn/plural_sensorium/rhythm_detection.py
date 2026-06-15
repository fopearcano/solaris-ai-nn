"""Rhythm detection -- the recurring tempos of a peculiar sensorium.

A :class:`RhythmDetector` watches the timestamps of events from each source and
extracts a :class:`RhythmSignature` when the inter-event intervals become regular
enough. Rhythms are modality-native (an RF burst cadence, a machine-state cycle,
a vibration tempo); they are never assumed to mean a human concept.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RhythmSignature:
    """A detected recurring tempo for one source/modality."""

    source_id: str
    modality: str
    period: float
    regularity: float  # 1.0 = perfectly regular
    cycles: int
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class RhythmDetector:
    """Extracts rhythm signatures from per-source event timing."""

    min_cycles: int = 3
    regularity_threshold: float = 0.6
    _timestamps: Dict[str, List[float]] = field(default_factory=dict)
    _modality: Dict[str, str] = field(default_factory=dict)
    signatures: Dict[str, RhythmSignature] = field(default_factory=dict)

    def observe(self, source_id: str, modality: str, timestamp: float) -> None:
        self._timestamps.setdefault(source_id, []).append(timestamp)
        self._timestamps[source_id] = self._timestamps[source_id][-50:]
        self._modality[source_id] = modality

    def detect(self, source_id: str) -> Optional[RhythmSignature]:
        stamps = sorted(self._timestamps.get(source_id, []))
        if len(stamps) < self.min_cycles + 1:
            return None
        intervals = [b - a for a, b in zip(stamps, stamps[1:]) if b > a]
        if len(intervals) < self.min_cycles:
            return None
        mean = statistics.fmean(intervals)
        if mean <= 0:
            return None
        stdev = statistics.pstdev(intervals)
        regularity = max(0.0, 1.0 - (stdev / mean))
        if regularity < self.regularity_threshold:
            return None
        sig = RhythmSignature(
            source_id=source_id, modality=self._modality.get(source_id, ""),
            period=mean, regularity=regularity, cycles=len(intervals),
            provenance={"source_id": source_id,
                        "modality": self._modality.get(source_id, "")})
        self.signatures[source_id] = sig
        return sig

    def detect_all(self) -> List[RhythmSignature]:
        out: List[RhythmSignature] = []
        for source_id in self._timestamps:
            sig = self.detect(source_id)
            if sig is not None:
                out.append(sig)
        return out

    def rhythm_pressure(self) -> float:
        return min(1.0, len(self.signatures) / 4.0) if self.signatures else 0.0

    def snapshot(self) -> Dict[str, Any]:
        return {"rhythm_signature_count": len(self.signatures),
                "signatures": [s.to_dict() for s in self.signatures.values()]}
