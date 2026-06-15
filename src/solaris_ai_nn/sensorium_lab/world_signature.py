"""World signature -- the observable structural fingerprint of a built world.

A :class:`SensoriumWorldSignature` summarises the internal *structure* Solaris
built under one sensorium: modality distribution, pressure profile, the families
of symbols / hypotheses / relations it formed, its grounding and contamination,
and its uncertainty. It is **not** subjective experience and **not** qualia: it
does not describe "what Solaris feels". It is an observable fingerprint, used only
to compare sensoriums structurally.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SensoriumWorldSignature:
    """An observable structural fingerprint of one sensorium arm."""

    arm_id: str
    condition: str
    modality_distribution: Dict[str, int] = field(default_factory=dict)
    dominant_receptor_families: List[str] = field(default_factory=list)
    field_pressure_profile: Dict[str, float] = field(default_factory=dict)
    baseline_shift_count: int = 0
    absence_sensitivity: float = 0.0
    rhythm_count: int = 0
    invariant_count: int = 0
    cross_modal_relation_count: int = 0
    proto_symbol_family_distribution: Dict[str, int] = field(
        default_factory=dict)
    world_node_distribution: Dict[str, int] = field(default_factory=dict)
    hypothesis_family_distribution: Dict[str, int] = field(default_factory=dict)
    logos_tension_distribution: Dict[str, int] = field(default_factory=dict)
    attention_strategy_profile: Dict[str, int] = field(default_factory=dict)
    changed_perception_score: float = 0.0
    modality_native_grounding_score: float = 0.0
    human_label_contamination_score: float = 0.0
    uncertainty_profile: float = 0.0
    limitations: List[str] = field(default_factory=lambda: [
        "An observable structural fingerprint, not subjective experience.",
        "Not qualia; this does not describe what Solaris feels.",
    ])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "arm_id": self.arm_id,
            "condition": self.condition,
            "modality_distribution": dict(self.modality_distribution),
            "dominant_receptor_families": list(self.dominant_receptor_families),
            "field_pressure_profile": dict(self.field_pressure_profile),
            "baseline_shift_count": self.baseline_shift_count,
            "absence_sensitivity": self.absence_sensitivity,
            "rhythm_count": self.rhythm_count,
            "invariant_count": self.invariant_count,
            "cross_modal_relation_count": self.cross_modal_relation_count,
            "proto_symbol_family_distribution":
                dict(self.proto_symbol_family_distribution),
            "world_node_distribution": dict(self.world_node_distribution),
            "hypothesis_family_distribution":
                dict(self.hypothesis_family_distribution),
            "logos_tension_distribution": dict(self.logos_tension_distribution),
            "attention_strategy_profile": dict(self.attention_strategy_profile),
            "changed_perception_score": self.changed_perception_score,
            "modality_native_grounding_score":
                self.modality_native_grounding_score,
            "human_label_contamination_score":
                self.human_label_contamination_score,
            "uncertainty_profile": self.uncertainty_profile,
            "limitations": list(self.limitations),
            "note": "observable structural fingerprint; not subjective "
                    "experience, not qualia",
        }


@dataclass
class WorldSignatureBuilder:
    """Builds a world signature from a completed runtime."""

    def build(self, arm_id: str, condition: str, runtime: Any, *,
              probe_result: Any = None) -> SensoriumWorldSignature:
        rt = runtime
        if rt is None:
            return SensoriumWorldSignature(arm_id=arm_id, condition=condition)

        modality_dist: Dict[str, int] = {}
        for receptor in rt.receptors.values():
            modality_dist[receptor.modality] = modality_dist.get(
                receptor.modality, 0) + receptor.event_count
        dominant = sorted(modality_dist, key=modality_dist.get,
                          reverse=True)[:3]

        proto_families: Dict[str, int] = {}
        for proto in rt.proto_symbol_candidates:
            t = proto.get("symbol_type", "unknown")
            proto_families[t] = proto_families.get(t, 0) + 1

        node_dist: Dict[str, int] = {}
        for struct in rt.world_model_structures:
            kind = struct.get("kind", "unknown")
            node_dist[kind] = node_dist.get(kind, 0) + 1

        hyp_dist: Dict[str, int] = {}
        for hyp in rt.hypotheses:
            kind = hyp.get("kind", "unknown")
            hyp_dist[kind] = hyp_dist.get(kind, 0) + 1

        tension_dist: Dict[str, int] = {}
        for t in rt.logos_tensions:
            name = t.get("tension", "unknown")
            tension_dist[name] = tension_dist.get(name, 0) + 1

        attention_dist: Dict[str, int] = {}
        for shift in rt.attention.history:
            attention_dist[shift.action] = attention_dist.get(
                shift.action, 0) + 1

        pressures = rt.sensory_field.to_dict().get("pressures", {})
        score = (probe_result.changed_perception_score
                 if probe_result is not None else 0.0)

        return SensoriumWorldSignature(
            arm_id=arm_id, condition=condition,
            modality_distribution=modality_dist,
            dominant_receptor_families=dominant,
            field_pressure_profile={k: round(float(v), 4)
                                    for k, v in pressures.items()},
            baseline_shift_count=len(rt.baseline_shifts),
            absence_sensitivity=round(pressures.get("absence", 0.0), 4),
            rhythm_count=len(rt.rhythm.signatures),
            invariant_count=len(rt.invariants.candidates),
            cross_modal_relation_count=rt.cross_modal.relation_count(),
            proto_symbol_family_distribution=proto_families,
            world_node_distribution=node_dist,
            hypothesis_family_distribution=hyp_dist,
            logos_tension_distribution=tension_dist,
            attention_strategy_profile=attention_dist,
            changed_perception_score=score,
            modality_native_grounding_score=rt.modality_native_grounding_score(),
            human_label_contamination_score=rt.human_label_contamination_score(),
            uncertainty_profile=round(pressures.get("uncertainty", 0.0), 4))


@dataclass
class WorldSignatureComparison:
    """Structural difference between two world signatures (not metaphysical)."""

    def compare(self, a: SensoriumWorldSignature,
                b: SensoriumWorldSignature) -> Dict[str, Any]:
        def keyset(d: Dict[str, int]) -> set:
            return set(d)

        proto_overlap = keyset(a.proto_symbol_family_distribution) & keyset(
            b.proto_symbol_family_distribution)
        proto_union = keyset(a.proto_symbol_family_distribution) | keyset(
            b.proto_symbol_family_distribution)
        proto_jaccard = (len(proto_overlap) / len(proto_union)
                         if proto_union else 1.0)
        return {
            "arm_a": a.arm_id, "arm_b": b.arm_id,
            "modality_overlap": sorted(
                set(a.modality_distribution) & set(b.modality_distribution)),
            "proto_family_jaccard": round(proto_jaccard, 4),
            "changed_perception_delta": round(
                abs(a.changed_perception_score - b.changed_perception_score),
                4),
            "contamination_delta": round(
                abs(a.human_label_contamination_score
                    - b.human_label_contamination_score), 4),
            "grounding_delta": round(
                abs(a.modality_native_grounding_score
                    - b.modality_native_grounding_score), 4),
            "note": "structural difference only; not a ranking, not a "
                    "metaphysical comparison",
        }
