"""Anomalies -- controlled developmental perturbations, not errors.

A repeated pattern suddenly breaks; an expected consequence fails to
arrive; a reward analogue turns neutral; danger appears in a safe
context. These stress prediction, Mysterium, the world model, and
proto-language -- and they are logged as ordinary ecology events, never
as system errors. Anomaly rate is bounded.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class AnomalyKind:
    EXPECTED_SIGNAL_MISSING = "expected_signal_missing"
    EXPECTED_CONSEQUENCE_ABSENT = "expected_consequence_absent"
    REWARD_TURNS_NEUTRAL = "reward_turns_neutral"
    DANGER_IN_SAFE_CONTEXT = "danger_in_safe_context"
    SEQUENCE_BREAK = "sequence_break"
    DELAYED_CONSEQUENCE_SHIFT = "delayed_consequence_shift"
    INTENSITY_INVERSION = "intensity_inversion"
    BOUNDARY_APPEARS_DISAPPEARS = "boundary_appears_disappears"

    ALL = (EXPECTED_SIGNAL_MISSING, EXPECTED_CONSEQUENCE_ABSENT,
           REWARD_TURNS_NEUTRAL, DANGER_IN_SAFE_CONTEXT,
           SEQUENCE_BREAK, DELAYED_CONSEQUENCE_SHIFT,
           INTENSITY_INVERSION, BOUNDARY_APPEARS_DISAPPEARS)


@dataclass
class AnomalyGenerator:
    """Bounded, deterministic, logged perturbations."""

    rng: Any = None
    max_anomalies: int = 200
    anomalies: List[Dict[str, Any]] = field(default_factory=list)
    by_kind: Dict[str, int] = field(default_factory=dict)
    capped: int = field(default=0, init=False)

    def maybe_anomaly(self, step: int, probability: float,
                      established_pattern: Optional[str] = None,
                      ) -> Optional[Dict[str, Any]]:
        """Produce an anomaly with the given probability (bounded)."""
        if self.rng is None or self.rng.random() >= max(
                0.0, min(0.5, probability)):
            return None
        if len(self.anomalies) >= self.max_anomalies:
            self.capped += 1
            return None
        # Prefer a sequence break when there is an established pattern.
        if established_pattern is not None and self.rng.random() < 0.5:
            kind = AnomalyKind.SEQUENCE_BREAK
        else:
            kind = self.rng.choice(list(AnomalyKind.ALL))
        record = {
            "kind": kind, "step": step,
            "broke_pattern": established_pattern,
            "anomaly_id": f"ANOM_{len(self.anomalies) + 1:04d}",
            # Anomalies raise novelty/unknown but are NOT errors.
            "novelty_hint": 0.9, "is_error": False}
        self.anomalies.append(record)
        self.by_kind[kind] = self.by_kind.get(kind, 0) + 1
        self.anomalies = self.anomalies[-self.max_anomalies:]
        return record

    def snapshot(self) -> Dict[str, Any]:
        return {
            "anomaly_count": len(self.anomalies),
            "by_kind": dict(self.by_kind),
            "capped": self.capped,
            "recent": self.anomalies[-5:],
            "note": "anomalies are controlled perturbations, not errors",
        }
