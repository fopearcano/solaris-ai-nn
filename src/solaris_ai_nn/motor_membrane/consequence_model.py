"""Action consequence model -- predicted vs observed simulated outcomes.

The :class:`ConsequenceModel` records, per action, an expected outcome and the
observed (simulated/internal) outcome, and scores prediction accuracy.
Consequences are simulation/internal outcomes only; prediction failures can
feed the hypothesis engine and LOGOS, and confirmed consequences can feed
habit learning and the world model.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ActionConsequencePrediction:
    """What a motor action is expected to do (before execution)."""

    action_id: str
    expected_state_change: bool = False
    expected_reaction_valence: float = 0.0
    expected_information_gain: float = 0.0
    mysterium_before: float = 0.0
    world_model_confidence_before: float = 0.0
    proto_symbol_ambiguity_before: float = 0.0
    energy_before: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ActionConsequenceRecord:
    """Predicted vs observed simulated consequence for one action."""

    action_id: str
    expected_state_change: bool = False
    observed_state_change: bool = False
    expected_reaction_valence: float = 0.0
    observed_reaction_valence: float = 0.0
    expected_information_gain: float = 0.0
    observed_information_gain: float = 0.0
    mysterium_before: float = 0.0
    mysterium_after: float = 0.0
    world_model_confidence_before: float = 0.0
    world_model_confidence_after: float = 0.0
    proto_symbol_ambiguity_before: float = 0.0
    proto_symbol_ambiguity_after: float = 0.0
    energy_before: float = 0.0
    energy_after: float = 0.0
    safety_outcome: str = "safe"
    simulated: bool = True
    timestamp: float = field(default_factory=time.time)

    @property
    def prediction_correct(self) -> bool:
        return (self.expected_state_change == self.observed_state_change
                and abs(self.expected_reaction_valence
                        - self.observed_reaction_valence) <= 0.4)

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__),
                "prediction_correct": self.prediction_correct}


@dataclass
class ConsequenceModel:
    """Predicts and records simulated action consequences."""

    predictions: Dict[str, ActionConsequencePrediction] = field(
        default_factory=dict)
    records: List[ActionConsequenceRecord] = field(default_factory=list)

    def predict(self, action: Any,
                situation: Optional[Dict[str, Any]] = None,
                ) -> ActionConsequencePrediction:
        sit = dict(situation or {})
        pred = ActionConsequencePrediction(
            action_id=action.action_id,
            expected_state_change=action.action_type.startswith("move")
            or action.action_type in ("touch_simulated_object",
                                      "pick_simulated_object"),
            expected_reaction_valence=float(
                getattr(action, "metadata", {}).get("expected_valence", 0.0)),
            expected_information_gain=float(action.expected_information_gain),
            mysterium_before=float(sit.get("mysterium_pressure", 0.0) or 0.0),
            world_model_confidence_before=float(
                sit.get("world_model_confidence", 0.0) or 0.0),
            proto_symbol_ambiguity_before=float(
                sit.get("proto_symbol_ambiguity", 0.0) or 0.0),
            energy_before=float(sit.get("energy", 0.0) or 0.0))
        self.predictions[action.action_id] = pred
        return pred

    def record(self, action_id: str, result: Any,
               situation_after: Optional[Dict[str, Any]] = None,
               ) -> ActionConsequenceRecord:
        sit = dict(situation_after or {})
        pred = self.predictions.get(action_id) or \
            ActionConsequencePrediction(action_id=action_id)
        rec = ActionConsequenceRecord(
            action_id=action_id,
            expected_state_change=pred.expected_state_change,
            observed_state_change=bool(getattr(result, "state_changed", False)),
            expected_reaction_valence=pred.expected_reaction_valence,
            observed_reaction_valence=float(
                getattr(result, "reaction_valence", 0.0)),
            expected_information_gain=pred.expected_information_gain,
            observed_information_gain=float(
                getattr(result, "information_gain", 0.0)),
            mysterium_before=pred.mysterium_before,
            mysterium_after=float(sit.get("mysterium_pressure",
                                          pred.mysterium_before) or 0.0),
            world_model_confidence_before=pred.world_model_confidence_before,
            world_model_confidence_after=float(
                sit.get("world_model_confidence",
                        pred.world_model_confidence_before) or 0.0),
            proto_symbol_ambiguity_before=pred.proto_symbol_ambiguity_before,
            proto_symbol_ambiguity_after=float(
                sit.get("proto_symbol_ambiguity",
                        pred.proto_symbol_ambiguity_before) or 0.0),
            energy_before=pred.energy_before,
            energy_after=float(sit.get("energy", pred.energy_before) or 0.0),
            safety_outcome=str(sit.get("safety_outcome", "safe")),
            simulated=bool(getattr(result, "simulated", True)))
        self.records.append(rec)
        self.records = self.records[-2000:]
        return rec

    def prediction_accuracy(self) -> float:
        if not self.records:
            return 0.0
        correct = sum(1 for r in self.records if r.prediction_correct)
        return round(correct / len(self.records), 4)

    def hypothesis_seeds(self) -> List[str]:
        """Mispredictions are seeds for the hypothesis engine (sim-scoped)."""
        return [f"action_consequence::{r.action_id}" for r in self.records
                if not r.prediction_correct][-16:]

    def snapshot(self) -> Dict[str, Any]:
        return {
            "record_count": len(self.records),
            "prediction_accuracy": self.prediction_accuracy(),
            "hypothesis_seed_count": len(self.hypothesis_seeds()),
            "recent": [r.to_dict() for r in self.records[-8:]],
        }
