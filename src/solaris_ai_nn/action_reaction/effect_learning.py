"""Effect learning -- provisional action->reaction relations from repeated evidence.

The :class:`EffectLearningEngine` accumulates evidence that an action kind tends to
produce a reaction kind. Effects are provisional, correlation is never causation,
stronger confidence requires repeated evidence, and failed effects remain visible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


@dataclass
class ActionEffectModel:
    """The learned (provisional) relation between an action kind and reactions."""

    action_kind: str
    reaction_counts: Dict[str, int] = field(default_factory=dict)
    observations: int = 0
    success_observations: int = 0

    def observe(self, reaction_kind: str, *, constructive: bool) -> None:
        self.reaction_counts[reaction_kind] = self.reaction_counts.get(
            reaction_kind, 0) + 1
        self.observations += 1
        if constructive:
            self.success_observations += 1

    @property
    def dominant_reaction(self) -> str:
        if not self.reaction_counts:
            return "unknown"
        return max(self.reaction_counts, key=self.reaction_counts.get)

    @property
    def confidence(self) -> float:
        # Confidence grows with repeated evidence (saturating).
        return round(min(1.0, 0.2 * self.observations), 4)

    @property
    def success_rate(self) -> float:
        if not self.observations:
            return 0.0
        return round(self.success_observations / self.observations, 4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_kind": self.action_kind,
            "dominant_reaction": self.dominant_reaction,
            "reaction_counts": dict(self.reaction_counts),
            "observations": self.observations,
            "confidence": self.confidence,
            "success_rate": self.success_rate,
            "note": "provisional effect; correlation is not causation; failed "
                    "effects remain visible",
        }


@dataclass
class EffectLearningResult:
    action_kind: str
    reaction_kind: str
    confidence: float
    success_rate: float

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


_CONSTRUCTIVE_VALENCES = frozenset({"constructive", "stabilizing"})


@dataclass
class EffectLearningEngine:
    """Learns provisional action->reaction effect models from observations."""

    models: Dict[str, ActionEffectModel] = field(default_factory=dict)

    def observe(self, action_kind: str, reaction_kind: str,
                reaction_valence: str) -> EffectLearningResult:
        model = self.models.get(action_kind)
        if model is None:
            model = ActionEffectModel(action_kind=action_kind)
            self.models[action_kind] = model
        model.observe(reaction_kind,
                      constructive=reaction_valence in _CONSTRUCTIVE_VALENCES)
        return EffectLearningResult(
            action_kind=action_kind, reaction_kind=reaction_kind,
            confidence=model.confidence, success_rate=model.success_rate)

    def learned_count(self) -> int:
        return sum(1 for m in self.models.values() if m.observations >= 2)

    def low_effect_actions(self) -> List[str]:
        """Action kinds with repeated low success (candidates to avoid)."""
        return [k for k, m in self.models.items()
                if m.observations >= 2 and m.success_rate < 0.3]

    def to_dict(self) -> Dict[str, Any]:
        return {"effect_model_count": len(self.models),
                "learned_count": self.learned_count(),
                "models": [m.to_dict() for m in self.models.values()]}
