"""Organismic continuity -- trace continuity across ticks/runs, not biological life.

:class:`OrganismicContinuity` tracks :class:`ContinuityAnchor`s (heartbeat,
receptor, field, memory, sign, concept, source rhythm, self-boundary, restart,
absence) and logs :class:`ContinuityBreak`s. Continuity here is trace continuity,
NOT biological life; breaks are logged, and recovery does not erase break history.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


class ContinuityAnchorType:
    HEARTBEAT = "heartbeat_tick"
    RECEPTOR = "receptor"
    SENSORY_FIELD = "sensory_field"
    MEMORY = "memory"
    SIGN = "sign"
    CONCEPT = "concept"
    SOURCE_RHYTHM = "source_rhythm"
    SELF_BOUNDARY = "self_boundary"
    RESTART = "restart"
    ABSENCE = "absence"

    ALL = (HEARTBEAT, RECEPTOR, SENSORY_FIELD, MEMORY, SIGN, CONCEPT,
           SOURCE_RHYTHM, SELF_BOUNDARY, RESTART, ABSENCE)


class ContinuityBreakType:
    UNGRACEFUL_SHUTDOWN = "ungraceful_shutdown"
    MISSING_STATE = "missing_state"
    SOURCE_SILENCE = "source_silence"
    FEEDER_CORRUPTION = "feeder_corruption"
    RECEPTOR_RESET = "receptor_reset"
    MEMORY_GAP = "memory_gap"
    SIGN_DRIFT_SHOCK = "sign_drift_shock"
    FAILED_RECOVERY = "failed_recovery"
    UNKNOWN = "unknown_discontinuity"

    ALL = (UNGRACEFUL_SHUTDOWN, MISSING_STATE, SOURCE_SILENCE,
           FEEDER_CORRUPTION, RECEPTOR_RESET, MEMORY_GAP, SIGN_DRIFT_SHOCK,
           FAILED_RECOVERY, UNKNOWN)


@dataclass
class ContinuityAnchor:
    anchor_type: str
    ref: str = ""
    strength: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {"anchor_type": self.anchor_type, "ref": self.ref,
                "strength": round(self.strength, 4)}


@dataclass
class ContinuityBreak:
    break_type: str
    detail: str = ""
    break_id: str = field(default_factory=lambda: f"BRK_{uuid.uuid4().hex[:8]}")
    recovered: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"break_id": self.break_id, "break_type": self.break_type,
                "detail": self.detail, "recovered": self.recovered,
                "note": "trace-continuity break; logged and retained"}


@dataclass
class ContinuityRecovery:
    break_id: str
    anchor_type: str
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"break_id": self.break_id, "anchor_type": self.anchor_type,
                "detail": self.detail,
                "note": "recovery does not erase the break history"}


@dataclass
class OrganismicContinuity:
    """Operational trace continuity (not biological life)."""

    anchors: List[ContinuityAnchor] = field(default_factory=list)
    breaks: List[ContinuityBreak] = field(default_factory=list)
    recoveries: List[ContinuityRecovery] = field(default_factory=list)

    def anchor(self, anchor_type: str, ref: str = "",
               strength: float = 1.0) -> ContinuityAnchor:
        a = ContinuityAnchor(anchor_type=anchor_type, ref=ref,
                             strength=strength)
        self.anchors.append(a)
        return a

    def record_break(self, break_type: str, detail: str = "") -> ContinuityBreak:
        b = ContinuityBreak(break_type=break_type, detail=detail)
        self.breaks.append(b)
        return b

    def recover(self, break_id: str, anchor_type: str,
                detail: str = "") -> ContinuityRecovery:
        """Mark a break recovered WITHOUT removing it from the break log."""
        for b in self.breaks:
            if b.break_id == break_id:
                b.recovered = True
        rec = ContinuityRecovery(break_id=break_id, anchor_type=anchor_type,
                                 detail=detail)
        self.recoveries.append(rec)
        return rec

    def continuity_score(self) -> float:
        if not self.anchors:
            return 0.0
        base = sum(a.strength for a in self.anchors) / len(self.anchors)
        # Unrecovered breaks reduce continuity.
        unrecovered = sum(1 for b in self.breaks if not b.recovered)
        return round(max(0.0, base - 0.1 * unrecovered), 4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anchor_count": len(self.anchors),
            "break_count": len(self.breaks),
            "recovery_count": len(self.recoveries),
            "continuity_score": self.continuity_score(),
            "anchors": [a.to_dict() for a in self.anchors],
            "breaks": [b.to_dict() for b in self.breaks],
            "recoveries": [r.to_dict() for r in self.recoveries],
            "note": "trace continuity, not biological life; breaks are retained "
                    "even after recovery",
        }
