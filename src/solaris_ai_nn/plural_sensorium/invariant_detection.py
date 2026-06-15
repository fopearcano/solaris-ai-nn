"""Invariant detection -- the stable structures that may become proto-symbols.

A :class:`InvariantDetector` looks for stable, recurring structure in the stream:
a repeated burst pattern, a stable frequency island, a recurring boundary, a
machine-state cycle, an absence-after-pattern. These :class:`InvariantCandidate`s
are not human concepts; they are modality-native regularities that *may* later
become proto-symbol candidates. Source and modality are always preserved.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class InvariantKind:
    REPEATED_BURST = "repeated_burst"
    STABLE_FREQUENCY_ISLAND = "stable_frequency_island"
    REPEATING_BOUNDARY = "repeating_boundary"
    RECURRING_VIBRATION_SIGNATURE = "recurring_vibration_signature"
    REPEATED_THERMAL_GRADIENT = "repeated_thermal_gradient"
    MAGNETIC_ANOMALY_CYCLE = "magnetic_anomaly_cycle"
    TEXT_LOG_RHYTHM = "text_log_rhythm"
    MACHINE_STATE_RHYTHM = "machine_state_rhythm"
    ABSENCE_AFTER_PATTERN = "absence_after_pattern"
    PATTERN_BEFORE_NOISE = "pattern_before_noise"
    CROSS_MODAL_RHYTHM = "cross_modal_rhythm"

    ALL = (REPEATED_BURST, STABLE_FREQUENCY_ISLAND, REPEATING_BOUNDARY,
           RECURRING_VIBRATION_SIGNATURE, REPEATED_THERMAL_GRADIENT,
           MAGNETIC_ANOMALY_CYCLE, TEXT_LOG_RHYTHM, MACHINE_STATE_RHYTHM,
           ABSENCE_AFTER_PATTERN, PATTERN_BEFORE_NOISE, CROSS_MODAL_RHYTHM)


@dataclass
class SensoriumInvariant:
    """A confirmed, stable invariant (a strong, repeated structure)."""

    invariant_id: str
    kind: str
    modality: str
    source_id: str
    support: int
    signature: str
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class InvariantCandidate:
    """A provisional invariant, retained with its modality and provenance."""

    candidate_id: str
    kind: str
    modality: str
    source_id: str
    support: int
    signature: str
    provenance: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_strong(self) -> bool:
        return self.support >= 3

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__), "is_strong": self.is_strong}


def _signature(modality: str, bucket: Any) -> str:
    return f"{modality}:{bucket}"


@dataclass
class InvariantDetector:
    """Finds recurring modality-native structures (provenance preserved)."""

    min_support: int = 2
    # signature -> (kind, modality, source_id, support)
    _seen: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    candidates: Dict[str, InvariantCandidate] = field(default_factory=dict)

    def observe_feature_bucket(self, source_id: str, modality: str,
                               kind: str, bucket: Any) -> Optional[
                                   InvariantCandidate]:
        """Record an occurrence; promote to a candidate at enough support."""
        sig = _signature(modality, bucket)
        entry = self._seen.setdefault(
            sig, {"kind": kind, "modality": modality, "source_id": source_id,
                  "support": 0})
        entry["support"] += 1
        if entry["support"] >= self.min_support:
            cand = self.candidates.get(sig)
            if cand is None:
                cand = InvariantCandidate(
                    candidate_id=f"INV_{uuid.uuid4().hex[:8]}", kind=kind,
                    modality=modality, source_id=source_id,
                    support=entry["support"], signature=sig,
                    provenance={"source_id": source_id, "modality": modality})
                self.candidates[sig] = cand
            else:
                cand.support = entry["support"]
            return cand
        return None

    def observe_rhythm(self, source_id: str, modality: str,
                       period: float) -> Optional[InvariantCandidate]:
        """A detected rhythm is a recurrence invariant; bucket the period."""
        kind = (InvariantKind.MACHINE_STATE_RHYTHM
                if modality == "machine_rhythm" else
                InvariantKind.TEXT_LOG_RHYTHM
                if modality == "human_textual" else
                InvariantKind.RECURRING_VIBRATION_SIGNATURE
                if modality == "vibration" else InvariantKind.REPEATED_BURST)
        bucket = f"period~{round(period, 1)}"
        return self.observe_feature_bucket(source_id, modality, kind, bucket)

    def strong_candidates(self) -> List[InvariantCandidate]:
        return [c for c in self.candidates.values() if c.is_strong]

    def confirmed(self) -> List[SensoriumInvariant]:
        return [SensoriumInvariant(
            invariant_id=c.candidate_id, kind=c.kind, modality=c.modality,
            source_id=c.source_id, support=c.support, signature=c.signature,
            provenance=dict(c.provenance)) for c in self.strong_candidates()]

    def snapshot(self) -> Dict[str, Any]:
        return {"invariant_candidate_count": len(self.candidates),
                "strong_invariant_count": len(self.strong_candidates()),
                "candidates": [c.to_dict() for c in self.candidates.values()]}
