"""Changed future perception -- did exposure change the internal response?

:class:`PerceptionChangeProbe` compares the organism's *early* response to a
stimulus against its *late* response to a similar stimulus, across modalities and
across the perceptual machinery (receptors, baselines, novelty, absence,
attention, invariants, proto-symbols, hypotheses, world-model relations). A
positive result is evidence of changed internal response *structure* -- it is not
evidence of consciousness, understanding, or sentience, and a no-change result is
reported honestly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

_PROBED_MODALITIES = ("radio_frequency", "ultrasound_echo", "vibration")
_DELTA_THRESHOLD = 1e-6


@dataclass
class PerceptionChangeMetric:
    name: str
    early: float
    late: float

    @property
    def delta(self) -> float:
        return self.late - self.early

    @property
    def changed(self) -> bool:
        return abs(self.delta) > _DELTA_THRESHOLD

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "early": self.early, "late": self.late,
                "delta": self.delta, "changed": self.changed}


@dataclass
class PerceptionChangeResult:
    metrics: List[PerceptionChangeMetric] = field(default_factory=list)
    per_modality: Dict[str, Any] = field(default_factory=dict)
    changed_perception_score: float = 0.0
    changed: bool = False
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metrics": [m.to_dict() for m in self.metrics],
            "per_modality": self.per_modality,
            "changed_perception_score": self.changed_perception_score,
            "changed": self.changed,
            "notes": list(self.notes),
            "disclaimer": "evidence of changed internal response structure "
                          "only; not consciousness, understanding, or sentience",
        }


@dataclass
class PerceptionChangeProbe:
    """Computes early-vs-late perceptual deltas from a completed run."""

    def compute(self, modality_responses: Dict[str, List[Dict[str, Any]]],
                runtime: Any) -> PerceptionChangeResult:
        metrics: List[PerceptionChangeMetric] = []
        per_modality: Dict[str, Any] = {}

        sens_deltas: List[float] = []
        base_deltas: List[float] = []
        nov_deltas: List[float] = []
        for modality in _PROBED_MODALITIES:
            responses = modality_responses.get(modality, [])
            if len(responses) < 2:
                continue
            early, late = responses[0], responses[-1]
            sens_d = late.get("sensitivity", 0.0) - early.get("sensitivity", 0.0)
            base_d = late.get("baseline", 0.0) - early.get("baseline", 0.0)
            nov_d = late.get("novelty", 0.0) - early.get("novelty", 0.0)
            sens_deltas.append(abs(sens_d))
            base_deltas.append(abs(base_d))
            nov_deltas.append(abs(nov_d))
            per_modality[modality] = {
                "early": early, "late": late,
                "sensitivity_delta": sens_d, "baseline_delta": base_d,
                "novelty_response_delta": nov_d,
                "response_count": len(responses)}

        def mean(xs: List[float]) -> float:
            return round(sum(xs) / len(xs), 4) if xs else 0.0

        # Aggregate, machinery-wide deltas (early state is implicitly zero at
        # the start of the run; late state is the post-exposure count/level).
        metrics.append(PerceptionChangeMetric(
            "receptor_sensitivity_delta", 0.0, mean(sens_deltas)))
        metrics.append(PerceptionChangeMetric(
            "baseline_delta", 0.0, mean(base_deltas)))
        metrics.append(PerceptionChangeMetric(
            "novelty_response_delta", 0.0, mean(nov_deltas)))
        metrics.append(PerceptionChangeMetric(
            "absence_response_delta", 0.0,
            float(len(getattr(runtime.absence, "events", [])))))
        metrics.append(PerceptionChangeMetric(
            "attention_priority_delta", 0.0,
            float(getattr(runtime.attention.state, "shifts", 0))))
        metrics.append(PerceptionChangeMetric(
            "invariant_recognition_delta", 0.0,
            float(len(runtime.invariants.candidates))))
        metrics.append(PerceptionChangeMetric(
            "proto_symbol_association_delta", 0.0,
            float(len(runtime.proto_symbol_candidates))))
        metrics.append(PerceptionChangeMetric(
            "hypothesis_trigger_delta", 0.0, float(len(runtime.hypotheses))))
        metrics.append(PerceptionChangeMetric(
            "world_model_relation_delta", 0.0,
            float(runtime.cross_modal.relation_count())))

        changed_count = sum(1 for m in metrics if m.changed)
        score = round(changed_count / len(metrics), 4) if metrics else 0.0
        result = PerceptionChangeResult(
            metrics=metrics, per_modality=per_modality,
            changed_perception_score=score, changed=score > 0.0)
        if not result.changed:
            result.notes.append("No change in internal response structure was "
                                "detected; reported honestly as a null result.")
        else:
            result.notes.append(f"{changed_count}/{len(metrics)} response "
                                "dimensions changed after exposure.")
        return result
