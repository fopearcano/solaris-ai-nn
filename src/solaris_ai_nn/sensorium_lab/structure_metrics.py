"""Structure metrics -- observable structural proxies, never a mind score.

:class:`SensoriumStructureMetrics` computes structural proxies from a completed
:class:`PluralSensoriumRuntime` run: perceptual structure, proto-symbol structure,
world-model structure, hypothesis structure, changed-perception deltas, and
grounding/contamination. There is no consciousness, sentience, life, or
intelligence score -- only structural proxies for comparing sensoriums.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def _ratio(part: int, whole: int) -> float:
    return round(part / whole, 4) if whole else 0.0


@dataclass
class SensoriumStructureMetrics:
    """Grouped structural metrics for one sensorium arm."""

    perceptual: Dict[str, Any] = field(default_factory=dict)
    proto_symbol: Dict[str, Any] = field(default_factory=dict)
    world_model: Dict[str, Any] = field(default_factory=dict)
    hypothesis: Dict[str, Any] = field(default_factory=dict)
    changed_perception: Dict[str, Any] = field(default_factory=dict)
    grounding: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "perceptual": dict(self.perceptual),
            "proto_symbol": dict(self.proto_symbol),
            "world_model": dict(self.world_model),
            "hypothesis": dict(self.hypothesis),
            "changed_perception": dict(self.changed_perception),
            "grounding": dict(self.grounding),
            "note": "structural proxies only; no consciousness/sentience/life "
                    "score and no intelligence quotient",
        }

    def flat(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for group in (self.perceptual, self.proto_symbol, self.world_model,
                      self.hypothesis, self.changed_perception, self.grounding):
            out.update(group)
        return out

    @classmethod
    def compute(cls, runtime: Any,
                modality_responses: Optional[Dict[str, List[Dict[str, Any]]]]
                = None, probe_result: Any = None,
                passive: bool = False) -> "SensoriumStructureMetrics":
        if passive or runtime is None:
            return cls._passive()
        rt = runtime
        field_state = rt.sensory_field.state()
        pressures = rt.sensory_field.to_dict().get("pressures", {})

        perceptual = {
            "active_modality_count": len(rt.active_modalities()),
            "receptor_adaptation_count": sum(
                r.adaptation_count for r in rt.receptors.values()),
            "baseline_shift_count": len(rt.baseline_shifts),
            "sensory_field_pressure_variance": cls._variance(
                list(pressures.values())),
            "absence_pressure_mean": pressures.get("absence", 0.0),
            "novelty_pressure_mean": pressures.get("novelty", 0.0),
            "rhythm_pressure_mean": pressures.get("rhythm", 0.0),
            "cross_modal_pressure_mean": pressures.get("cross_modal", 0.0),
        }

        protos = rt.proto_symbol_candidates
        symbol_types = [p.get("symbol_type") for p in protos]
        contaminated = sum(1 for p in protos
                           if p.get("human_label_contaminated"))
        cross_modal_syms = sum(1 for t in symbol_types
                               if t == "cross_modal_symbol")
        strong_inv = len(rt.invariants.strong_candidates())
        total_inv = max(1, len(rt.invariants.candidates))
        proto_symbol = {
            "proto_symbol_count": len(protos),
            "modality_grounded_symbol_count": sum(
                1 for p in protos if not p.get("human_label_contaminated")),
            "cross_modal_symbol_count": cross_modal_syms,
            "human_label_contaminated_symbol_count": contaminated,
            "stable_symbol_ratio": _ratio(strong_inv, total_inv),
            "symbol_family_diversity": len(set(symbol_types)),
        }

        structures = rt.world_model_structures
        node_kinds = ("modality_source", "invariant_candidate")
        nodes = [s for s in structures if s.get("kind") in node_kinds]
        edges = [s for s in structures
                 if s.get("kind") == "cross_modal_relation"]
        total_nodes = max(1, len(nodes))
        world_model = {
            "world_node_count": len(nodes),
            "world_edge_count": len(edges) + rt.cross_modal.relation_count(),
            "modality_native_node_ratio": 1.0,  # the lab never makes object nodes
            "human_object_node_ratio": 0.0,
            "cross_modal_edge_ratio": _ratio(
                rt.cross_modal.relation_count(), total_nodes),
            "predictive_edge_count": sum(
                1 for r in rt.cross_modal.all_relations()
                if r.relation_type == "followed_by"),
            "contradiction_count": len(rt.cross_modal.relations) and sum(
                1 for t in rt.logos_tensions
                if "contradict" in str(t.get("tension", ""))),
        }

        hyps = rt.hypotheses
        total_h = max(1, len(hyps))
        absence_h = sum(1 for h in hyps
                        if h.get("kind") == "signal_disappearance")
        human_h = sum(1 for h in hyps if h.get("modality") == "human_textual")
        native_h = sum(1 for h in hyps
                       if h.get("modality") not in ("human_textual", None))
        hypothesis = {
            "hypothesis_count": len(hyps),
            "modality_native_hypothesis_ratio": _ratio(native_h, total_h),
            "absence_hypothesis_ratio": _ratio(absence_h, total_h),
            "cross_modal_hypothesis_ratio": _ratio(
                sum(1 for h in hyps if h.get("kind") == "cross_modal"), total_h),
            "human_label_dependent_hypothesis_ratio": _ratio(human_h, total_h),
        }

        changed = cls._changed(probe_result)

        grounding = {
            "modality_native_grounding_score":
                rt.modality_native_grounding_score(),
            "feature_dependence_score": round(
                1.0 - rt.human_label_contamination_score(), 4),
            "human_label_contamination_score":
                rt.human_label_contamination_score(),
            "external_uncertainty_score": pressures.get("uncertainty", 0.0),
            "fixture_overfit_warning_count": sum(
                1 for r in rt.grounding.records
                if r.quality == "overfit_to_fixture"),
        }
        return cls(perceptual=perceptual, proto_symbol=proto_symbol,
                   world_model=world_model, hypothesis=hypothesis,
                   changed_perception=changed, grounding=grounding)

    @staticmethod
    def _changed(probe_result: Any) -> Dict[str, Any]:
        if probe_result is None:
            return {"changed_perception_score": 0.0,
                    "receptor_sensitivity_delta": 0.0,
                    "attention_priority_delta": 0.0,
                    "novelty_response_delta": 0.0,
                    "absence_response_delta": 0.0,
                    "invariant_recognition_delta": 0.0}
        metrics = {m.name: round(m.late, 4) for m in probe_result.metrics}
        return {
            "changed_perception_score": probe_result.changed_perception_score,
            "receptor_sensitivity_delta": metrics.get(
                "receptor_sensitivity_delta", 0.0),
            "attention_priority_delta": metrics.get(
                "attention_priority_delta", 0.0),
            "novelty_response_delta": metrics.get(
                "novelty_response_delta", 0.0),
            "absence_response_delta": metrics.get(
                "absence_response_delta", 0.0),
            "invariant_recognition_delta": metrics.get(
                "invariant_recognition_delta", 0.0),
        }

    @staticmethod
    def _variance(values: List[float]) -> float:
        nums = [float(v) for v in values if isinstance(v, (int, float))]
        return round(statistics.pvariance(nums), 6) if len(nums) > 1 else 0.0

    @classmethod
    def _passive(cls) -> "SensoriumStructureMetrics":
        zero_p = {"active_modality_count": 0, "receptor_adaptation_count": 0,
                  "baseline_shift_count": 0,
                  "sensory_field_pressure_variance": 0.0,
                  "absence_pressure_mean": 0.0, "novelty_pressure_mean": 0.0,
                  "rhythm_pressure_mean": 0.0, "cross_modal_pressure_mean": 0.0}
        zero_s = {"proto_symbol_count": 0, "modality_grounded_symbol_count": 0,
                  "cross_modal_symbol_count": 0,
                  "human_label_contaminated_symbol_count": 0,
                  "stable_symbol_ratio": 0.0, "symbol_family_diversity": 0}
        zero_w = {"world_node_count": 0, "world_edge_count": 0,
                  "modality_native_node_ratio": 0.0,
                  "human_object_node_ratio": 0.0, "cross_modal_edge_ratio": 0.0,
                  "predictive_edge_count": 0, "contradiction_count": 0}
        zero_h = {"hypothesis_count": 0,
                  "modality_native_hypothesis_ratio": 0.0,
                  "absence_hypothesis_ratio": 0.0,
                  "cross_modal_hypothesis_ratio": 0.0,
                  "human_label_dependent_hypothesis_ratio": 0.0}
        zero_c = {"changed_perception_score": 0.0,
                  "receptor_sensitivity_delta": 0.0,
                  "attention_priority_delta": 0.0,
                  "novelty_response_delta": 0.0, "absence_response_delta": 0.0,
                  "invariant_recognition_delta": 0.0}
        zero_g = {"modality_native_grounding_score": 0.0,
                  "feature_dependence_score": 0.0,
                  "human_label_contamination_score": 0.0,
                  "external_uncertainty_score": 0.0,
                  "fixture_overfit_warning_count": 0}
        return cls(perceptual=zero_p, proto_symbol=zero_s, world_model=zero_w,
                   hypothesis=zero_h, changed_perception=zero_c,
                   grounding=zero_g)
