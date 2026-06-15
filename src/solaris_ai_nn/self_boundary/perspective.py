"""Perspective -- an operational frame of attention/perception, not a viewpoint.

:class:`SensoriumPerspective` tracks the current operational frame (active modality
viewpoint, dominant/neglected receptor frame, field pressure, attention focus,
uncertainty focus, prediction/memory/simulation horizons) and records
:class:`PerspectiveShift`s. This is an operational frame, NOT a subjective
point-of-view.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PerspectiveFrame:
    """One operational perception/attention frame (not a subjective viewpoint)."""

    active_modality: str = ""
    dominant_receptor: str = ""
    neglected_receptor: str = ""
    field_pressure: float = 0.0
    attention_focus: str = ""
    uncertainty_focus: str = ""
    prediction_horizon: int = 1
    memory_horizon: int = 0
    simulation_horizon: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "active_modality": self.active_modality,
            "dominant_receptor": self.dominant_receptor,
            "neglected_receptor": self.neglected_receptor,
            "field_pressure": round(self.field_pressure, 4),
            "attention_focus": self.attention_focus,
            "uncertainty_focus": self.uncertainty_focus,
            "prediction_horizon": self.prediction_horizon,
            "memory_horizon": self.memory_horizon,
            "simulation_horizon": self.simulation_horizon,
            "note": "operational frame of attention/perception, not a "
                    "subjective point-of-view",
        }

    def signature(self) -> str:
        return f"{self.active_modality}|{self.dominant_receptor}|" \
               f"{self.attention_focus}"


@dataclass
class PerspectiveShift:
    """A recorded change between two perspective frames."""

    shift_id: str = field(default_factory=lambda: f"PSH_{uuid.uuid4().hex[:8]}")
    from_signature: str = ""
    to_signature: str = ""
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SensoriumPerspective:
    """Maintains the current perspective frame and records shifts."""

    frame: PerspectiveFrame = field(default_factory=PerspectiveFrame)
    shifts: List[PerspectiveShift] = field(default_factory=list)
    _prev_signature: Optional[str] = field(default=None, init=False)

    def update(self, new_frame: PerspectiveFrame, *,
               reason: str = "") -> Optional[PerspectiveShift]:
        """Adopt a new frame; record a shift if the signature changed."""
        sig = new_frame.signature()
        shift = None
        if self._prev_signature is not None and self._prev_signature != sig:
            shift = PerspectiveShift(
                from_signature=self._prev_signature, to_signature=sig,
                reason=reason or "perspective change")
            self.shifts.append(shift)
        self.frame = new_frame
        self._prev_signature = sig
        return shift

    def attention_recommendation(self) -> str:
        """An internal attention recommendation derived from the frame."""
        if self.frame.uncertainty_focus:
            return f"inspect uncertainty around {self.frame.uncertainty_focus}"
        if self.frame.neglected_receptor:
            return f"revisit neglected receptor {self.frame.neglected_receptor}"
        return "maintain current frame"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frame": self.frame.to_dict(),
            "shift_count": len(self.shifts),
            "shifts": [s.to_dict() for s in self.shifts],
            "attention_recommendation": self.attention_recommendation(),
        }
