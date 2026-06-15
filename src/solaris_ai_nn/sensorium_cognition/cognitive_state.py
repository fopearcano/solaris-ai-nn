"""Cognitive state -- the operational snapshot of sign-based cognition.

:class:`SensoriumCognitiveState` is an *operational* snapshot of what the cognition
layer is currently working over (active signs/concepts/hypotheses/tensions/needs)
and the pressures it is under (uncertainty, anticipation, question, simulation,
synthesis, memory-retrieval). It is NOT a subjective mind-state, NOT human-language
thought, and any human-readable summary is a debug gloss only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class CognitiveFocus:
    """What cognition is currently attending to (operational, not attention-as-mind)."""

    active_signs: List[str] = field(default_factory=list)
    active_proto_concepts: List[str] = field(default_factory=list)
    active_hypotheses: List[str] = field(default_factory=list)
    active_logos_tensions: List[str] = field(default_factory=list)
    active_perceptual_needs: List[str] = field(default_factory=list)
    attention_recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "active_signs": list(self.active_signs),
            "active_proto_concepts": list(self.active_proto_concepts),
            "active_hypotheses": list(self.active_hypotheses),
            "active_logos_tensions": list(self.active_logos_tensions),
            "active_perceptual_needs": list(self.active_perceptual_needs),
            "attention_recommendation": self.attention_recommendation,
        }


@dataclass
class CognitivePressure:
    """The bounded operational pressures driving cognitive moves (not feelings)."""

    uncertainty: float = 0.0
    anticipation: float = 0.0
    question_pressure: float = 0.0
    simulation_pressure: float = 0.0
    synthesis_pressure: float = 0.0
    memory_retrieval_pressure: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "uncertainty": round(self.uncertainty, 4),
            "anticipation": round(self.anticipation, 4),
            "question_pressure": round(self.question_pressure, 4),
            "simulation_pressure": round(self.simulation_pressure, 4),
            "synthesis_pressure": round(self.synthesis_pressure, 4),
            "memory_retrieval_pressure": round(
                self.memory_retrieval_pressure, 4),
            "note": "operational pressures, not feelings or subjective states",
        }


@dataclass
class CognitiveContinuity:
    """Bounded continuity bookkeeping across cognitive ticks."""

    continuity_tick: int = 0
    cognitive_fatigue: float = 0.0
    cognitive_saturation: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "continuity_tick": self.continuity_tick,
            "cognitive_fatigue": round(self.cognitive_fatigue, 4),
            "cognitive_saturation": round(self.cognitive_saturation, 4),
        }


@dataclass
class SensoriumCognitiveState:
    """The operational state of sign-based cognition (not a subjective mind)."""

    focus: CognitiveFocus = field(default_factory=CognitiveFocus)
    pressure: CognitivePressure = field(default_factory=CognitivePressure)
    continuity: CognitiveContinuity = field(default_factory=CognitiveContinuity)
    unresolved_contradictions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def debug_summary(self) -> str:
        """A human-readable DEBUG gloss only (never the internal representation)."""
        f = self.focus
        return (f"[debug-gloss] focus: {len(f.active_signs)} signs, "
                f"{len(f.active_proto_concepts)} concepts; "
                f"question_pressure={round(self.pressure.question_pressure, 2)}; "
                f"unresolved={len(self.unresolved_contradictions)}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "focus": self.focus.to_dict(),
            "pressure": self.pressure.to_dict(),
            "continuity": self.continuity.to_dict(),
            "unresolved_contradictions": list(self.unresolved_contradictions),
            "debug_summary": self.debug_summary(),
            "metadata": dict(self.metadata),
            "note": "operational cognitive state over signs/concepts; NOT a "
                    "subjective mind-state and NOT human-language thought; any "
                    "human-readable summary is a debug gloss only",
        }
