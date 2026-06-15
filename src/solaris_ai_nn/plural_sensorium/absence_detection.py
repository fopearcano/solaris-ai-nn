"""Absence detection -- silence is perception, not the lack of it.

A :class:`AbsenceDetector` registers :class:`ExpectedSignal`s (a source that has
been recurring is *expected* to keep recurring) and emits an :class:`AbsenceEvent`
when an expected signal goes missing. Absence is first-class perception: it feeds
Mysterium, LOGOS, the hypothesis engine, memory, and the world model.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ExpectedSignal:
    """A signal the organism has learned to expect (by source/modality)."""

    source_id: str
    modality: str
    expected_interval: float = 1.0
    last_seen: float = 0.0
    confidence: float = 0.5
    observations: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class AbsenceEvent:
    """A detected absence of an expected signal."""

    source_id: str
    modality: str
    expected_interval: float
    elapsed: float
    detail: str = ""
    provenance: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    absence_id: str = field(default_factory=lambda: f"ABS_{uuid.uuid4().hex[:8]}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "absence_id": self.absence_id,
            "source_id": self.source_id,
            "modality": self.modality,
            "expected_interval": self.expected_interval,
            "elapsed": self.elapsed,
            "detail": self.detail,
            "provenance": dict(self.provenance),
            "timestamp": self.timestamp,
        }


@dataclass
class AbsenceDetector:
    """Learns expectations and detects when expected signals go missing."""

    miss_factor: float = 2.0
    expectations: Dict[str, ExpectedSignal] = field(default_factory=dict)
    events: List[AbsenceEvent] = field(default_factory=list, init=False)

    def observe(self, source_id: str, modality: str, timestamp: float) -> None:
        """Register that a signal was seen, updating its expected interval."""
        exp = self.expectations.get(source_id)
        if exp is None:
            self.expectations[source_id] = ExpectedSignal(
                source_id=source_id, modality=modality, last_seen=timestamp,
                observations=1)
            return
        if timestamp > exp.last_seen:
            interval = timestamp - exp.last_seen
            # Slow update of the expected interval.
            exp.expected_interval = 0.7 * exp.expected_interval + 0.3 * interval
            exp.last_seen = timestamp
        exp.observations += 1
        exp.confidence = min(1.0, exp.confidence + 0.1)

    def register_expectation(self, source_id: str, modality: str,
                             expected_interval: float,
                             last_seen: float = 0.0) -> ExpectedSignal:
        exp = ExpectedSignal(source_id=source_id, modality=modality,
                             expected_interval=expected_interval,
                             last_seen=last_seen, confidence=1.0, observations=5)
        self.expectations[source_id] = exp
        return exp

    def check(self, now: float) -> List[AbsenceEvent]:
        """Emit an AbsenceEvent for every expected signal now overdue."""
        out: List[AbsenceEvent] = []
        for exp in self.expectations.values():
            if exp.observations < 2 or exp.expected_interval <= 0:
                continue
            elapsed = now - exp.last_seen
            if elapsed > exp.expected_interval * self.miss_factor:
                ev = AbsenceEvent(
                    source_id=exp.source_id, modality=exp.modality,
                    expected_interval=exp.expected_interval, elapsed=elapsed,
                    detail=f"expected every {exp.expected_interval:.2f}s; "
                           f"silent for {elapsed:.2f}s",
                    provenance={"source_id": exp.source_id,
                                "modality": exp.modality})
                out.append(ev)
                self.events.append(ev)
        return out

    def absence_pressure(self) -> float:
        return min(1.0, len(self.events) / 5.0) if self.events else 0.0

    def snapshot(self) -> Dict[str, Any]:
        return {"expected_signal_count": len(self.expectations),
                "absence_event_count": len(self.events)}
