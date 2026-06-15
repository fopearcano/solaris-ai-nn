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
    # Perceptual-ontogenesis profile (Prompt 47); empty when not attached.
    concept_family_distribution: Dict[str, int] = field(default_factory=dict)
    concept_stability_profile: Dict[str, int] = field(default_factory=dict)
    concept_decay_profile: Dict[str, int] = field(default_factory=dict)
    concept_relation_profile: Dict[str, Any] = field(default_factory=dict)
    human_label_concept_contamination: float = 0.0
    modality_native_concept_ratio: float = 0.0
    # Semiogenesis profile (Prompt 48); empty/zero when not attached.
    sign_family_distribution: Dict[str, int] = field(default_factory=dict)
    modality_native_sign_ratio: float = 0.0
    cross_modal_sign_ratio: float = 0.0
    absence_sign_ratio: float = 0.0
    contaminated_sign_ratio: float = 0.0
    private_syntax_density: float = 0.0
    gloss_dependence_score: float = 0.0
    # Sensorium-cognition profile (Prompt 49); empty/zero when not attached.
    cognitive_move_distribution: Dict[str, int] = field(default_factory=dict)
    prediction_profile: Dict[str, Any] = field(default_factory=dict)
    failed_prediction_profile: Dict[str, Any] = field(default_factory=dict)
    question_pressure_profile: Dict[str, Any] = field(default_factory=dict)
    simulation_profile: Dict[str, Any] = field(default_factory=dict)
    analogy_profile: Dict[str, Any] = field(default_factory=dict)
    synthesis_profile: Dict[str, Any] = field(default_factory=dict)
    # Self-boundary profile (Prompt 50); zero/empty when not attached.
    boundary_clarity_score: float = 0.0
    simulation_boundary_integrity: float = 0.0
    source_attribution_quality: float = 0.0
    perspective_shift_profile: Dict[str, Any] = field(default_factory=dict)
    receptor_body_schema_stability: float = 0.0
    continuity_break_count: int = 0
    identity_trace_density: float = 0.0
    # Desire-formation profile (Prompt 51); empty/zero when not attached.
    valence_profile: Dict[str, Any] = field(default_factory=dict)
    push_profile: Dict[str, Any] = field(default_factory=dict)
    desire_kind_distribution: Dict[str, int] = field(default_factory=dict)
    internal_action_profile: Dict[str, Any] = field(default_factory=dict)
    no_op_profile: Dict[str, Any] = field(default_factory=dict)
    conflict_profile: Dict[str, Any] = field(default_factory=dict)
    blocked_desire_count: int = 0
    desire_outcome_utility: float = 0.0
    # Action-reaction profile (Prompt 52); empty/zero when not attached.
    action_kind_distribution: Dict[str, int] = field(default_factory=dict)
    reaction_valence_distribution: Dict[str, int] = field(default_factory=dict)
    consequence_trace_profile: Dict[str, Any] = field(default_factory=dict)
    habit_profile: Dict[str, Any] = field(default_factory=dict)
    inhibition_profile: Dict[str, Any] = field(default_factory=dict)
    no_effect_action_profile: Dict[str, Any] = field(default_factory=dict)
    learned_policy_profile: Dict[str, Any] = field(default_factory=dict)
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
            "concept_family_distribution":
                dict(self.concept_family_distribution),
            "concept_stability_profile": dict(self.concept_stability_profile),
            "concept_decay_profile": dict(self.concept_decay_profile),
            "concept_relation_profile": dict(self.concept_relation_profile),
            "human_label_concept_contamination":
                self.human_label_concept_contamination,
            "modality_native_concept_ratio": self.modality_native_concept_ratio,
            "sign_family_distribution": dict(self.sign_family_distribution),
            "modality_native_sign_ratio": self.modality_native_sign_ratio,
            "cross_modal_sign_ratio": self.cross_modal_sign_ratio,
            "absence_sign_ratio": self.absence_sign_ratio,
            "contaminated_sign_ratio": self.contaminated_sign_ratio,
            "private_syntax_density": self.private_syntax_density,
            "gloss_dependence_score": self.gloss_dependence_score,
            "cognitive_move_distribution": dict(
                self.cognitive_move_distribution),
            "prediction_profile": dict(self.prediction_profile),
            "failed_prediction_profile": dict(self.failed_prediction_profile),
            "question_pressure_profile": dict(self.question_pressure_profile),
            "simulation_profile": dict(self.simulation_profile),
            "analogy_profile": dict(self.analogy_profile),
            "synthesis_profile": dict(self.synthesis_profile),
            "boundary_clarity_score": self.boundary_clarity_score,
            "simulation_boundary_integrity": self.simulation_boundary_integrity,
            "source_attribution_quality": self.source_attribution_quality,
            "perspective_shift_profile": dict(self.perspective_shift_profile),
            "receptor_body_schema_stability":
                self.receptor_body_schema_stability,
            "continuity_break_count": self.continuity_break_count,
            "identity_trace_density": self.identity_trace_density,
            "valence_profile": dict(self.valence_profile),
            "push_profile": dict(self.push_profile),
            "desire_kind_distribution": dict(self.desire_kind_distribution),
            "internal_action_profile": dict(self.internal_action_profile),
            "no_op_profile": dict(self.no_op_profile),
            "conflict_profile": dict(self.conflict_profile),
            "blocked_desire_count": self.blocked_desire_count,
            "desire_outcome_utility": self.desire_outcome_utility,
            "action_kind_distribution": dict(self.action_kind_distribution),
            "reaction_valence_distribution":
                dict(self.reaction_valence_distribution),
            "consequence_trace_profile": dict(self.consequence_trace_profile),
            "habit_profile": dict(self.habit_profile),
            "inhibition_profile": dict(self.inhibition_profile),
            "no_effect_action_profile": dict(self.no_effect_action_profile),
            "learned_policy_profile": dict(self.learned_policy_profile),
            "limitations": list(self.limitations),
            "note": "observable structural fingerprint; not subjective "
                    "experience, not qualia",
        }


@dataclass
class WorldSignatureBuilder:
    """Builds a world signature from a completed runtime."""

    def build(self, arm_id: str, condition: str, runtime: Any, *,
              probe_result: Any = None,
              ontogenesis: Any = None,
              semiogenesis: Any = None,
              cognition: Any = None,
              self_boundary: Any = None,
              desire_formation: Any = None,
              action_reaction: Any = None) -> SensoriumWorldSignature:
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

        # Perceptual-ontogenesis profile (optional).
        concept_families: Dict[str, int] = {}
        stability_profile: Dict[str, int] = {}
        decay_profile: Dict[str, int] = {}
        relation_profile: Dict[str, Any] = {}
        ont_contamination = 0.0
        ont_native_ratio = 0.0
        if ontogenesis is not None:
            ont_status = (ontogenesis.ontogenesis_status()
                          if hasattr(ontogenesis, "ontogenesis_status")
                          else ontogenesis if isinstance(ontogenesis, dict)
                          else {})
            if hasattr(ontogenesis, "family_builder"):
                concept_families = ontogenesis.family_builder.distribution()
            else:
                concept_families = ont_status.get(
                    "concept_family_distribution", {})
            stability_profile = {
                "stable": ont_status.get("stable_concept_count", 0),
                "candidate": max(
                    0, ont_status.get("proto_concept_count", 0)
                    - ont_status.get("stable_concept_count", 0)
                    - ont_status.get("decaying_concept_count", 0))}
            decay_profile = {
                "decaying": ont_status.get("decaying_concept_count", 0),
                "rejected": ont_status.get("rejected_concept_count", 0)}
            relation_profile = {
                "relation_count": ont_status.get("concept_relation_count", 0),
                "world_formation_density": ont_status.get(
                    "world_formation_density", 0.0)}
            ont_contamination = ont_status.get(
                "human_label_contamination_score", 0.0)
            ont_native_ratio = ont_status.get(
                "modality_native_concept_ratio", 0.0)

        # Semiogenesis profile (optional).
        sign_families: Dict[str, int] = {}
        sign_native_ratio = 0.0
        sign_cross_modal_ratio = 0.0
        sign_absence_ratio = 0.0
        sign_contaminated_ratio = 0.0
        syntax_density = 0.0
        gloss_dependence = 0.0
        if semiogenesis is not None:
            sem_status = (semiogenesis.semiogenesis_status()
                          if hasattr(semiogenesis, "semiogenesis_status")
                          else semiogenesis if isinstance(semiogenesis, dict)
                          else {})
            if hasattr(semiogenesis, "family_builder"):
                sign_families = semiogenesis.family_builder.distribution()
            sign_native_ratio = sem_status.get("modality_native_sign_ratio",
                                               0.0)
            sign_cross_modal_ratio = sem_status.get("cross_modal_sign_ratio",
                                                    0.0)
            sign_absence_ratio = sem_status.get("absence_sign_ratio", 0.0)
            sign_contaminated_ratio = sem_status.get("contaminated_sign_ratio",
                                                     0.0)
            patterns = sem_status.get("private_syntax_pattern_count", 0)
            signs = sem_status.get("internal_sign_count", 0)
            if signs >= 2:
                syntax_density = round(
                    min(1.0, patterns / (signs * (signs - 1) / 2)), 4)
            gloss_dependence = sem_status.get("gloss_dependence_score", 0.0)

        # Sensorium-cognition profile (optional).
        move_distribution: Dict[str, int] = {}
        prediction_profile: Dict[str, Any] = {}
        failed_prediction_profile: Dict[str, Any] = {}
        question_pressure_profile: Dict[str, Any] = {}
        simulation_profile: Dict[str, Any] = {}
        analogy_profile: Dict[str, Any] = {}
        synthesis_profile: Dict[str, Any] = {}
        if cognition is not None:
            cog_status = (cognition.cognition_status()
                          if hasattr(cognition, "cognition_status")
                          else cognition if isinstance(cognition, dict)
                          else {})
            if hasattr(cognition, "moves"):
                for mv in cognition.moves:
                    mt = getattr(mv, "move_type", "unknown")
                    move_distribution[mt] = move_distribution.get(mt, 0) + 1
            prediction_profile = {
                "count": cog_status.get("prediction_count", 0),
                "success_rate": cog_status.get("prediction_success_rate", 0.0)}
            failed_prediction_profile = {
                "count": cog_status.get("failed_prediction_count", 0)}
            question_pressure_profile = {
                "count": cog_status.get("question_pressure_count", 0)}
            simulation_profile = {
                "count": cog_status.get("internal_simulation_count", 0)}
            analogy_profile = {
                "count": cog_status.get("analogy_count", 0),
                "failures": cog_status.get("analogy_failure_count", 0)}
            synthesis_profile = {
                "count": cog_status.get("synthesis_count", 0)}

        # Self-boundary profile (optional).
        boundary_clarity = 0.0
        sim_integrity = 0.0
        source_quality = 0.0
        perspective_profile: Dict[str, Any] = {}
        body_stability = 0.0
        continuity_breaks = 0
        identity_density = 0.0
        if self_boundary is not None:
            sb_status = (self_boundary.self_boundary_status()
                         if hasattr(self_boundary, "self_boundary_status")
                         else self_boundary if isinstance(self_boundary, dict)
                         else {})
            boundary_clarity = sb_status.get("boundary_confidence_score", 0.0)
            sim_integrity = sb_status.get("simulation_boundary_integrity", 0.0)
            source_quality = round(
                1.0 - sb_status.get("source_attribution_uncertainty_score",
                                    0.0), 4)
            perspective_profile = {
                "shift_count": sb_status.get("perspective_shift_count", 0)}
            body_stability = sb_status.get("body_schema_stability", 0.0)
            continuity_breaks = sb_status.get("continuity_break_count", 0)
            identity_density = round(min(
                1.0, 0.05 * sb_status.get("identity_trace_event_count", 0)), 4)

        # Desire-formation profile (optional).
        valence_profile: Dict[str, Any] = {}
        push_profile: Dict[str, Any] = {}
        desire_kinds: Dict[str, int] = {}
        internal_action_profile: Dict[str, Any] = {}
        no_op_profile: Dict[str, Any] = {}
        conflict_profile: Dict[str, Any] = {}
        blocked_desires = 0
        desire_utility = 0.0
        if desire_formation is not None:
            df_status = (desire_formation.desire_status()
                         if hasattr(desire_formation, "desire_status")
                         else desire_formation
                         if isinstance(desire_formation, dict) else {})
            valence_profile = {
                "count": df_status.get("valence_gradient_count", 0),
                "dominant": df_status.get("dominant_valence_direction", "")}
            push_profile = {"count": df_status.get("push_count", 0)}
            if hasattr(desire_formation, "desires"):
                for d in desire_formation.desires:
                    k = getattr(d, "kind", "unknown")
                    desire_kinds[k] = desire_kinds.get(k, 0) + 1
            internal_action_profile = {
                "count": df_status.get("internal_action_count", 0)}
            no_op_profile = {"count": df_status.get("no_op_count", 0)}
            conflict_profile = {
                "count": df_status.get("desire_conflict_count", 0)}
            blocked_desires = df_status.get("safety_blocked_desire_count", 0)
            desire_utility = df_status.get("desire_outcome_success_rate", 0.0)

        # Action-reaction profile (optional).
        action_kinds: Dict[str, int] = {}
        reaction_valences: Dict[str, int] = {}
        consequence_profile: Dict[str, Any] = {}
        habit_profile: Dict[str, Any] = {}
        inhibition_profile: Dict[str, Any] = {}
        no_effect_profile: Dict[str, Any] = {}
        policy_profile: Dict[str, Any] = {}
        if action_reaction is not None:
            ar_status = (action_reaction.action_reaction_status()
                         if hasattr(action_reaction, "action_reaction_status")
                         else action_reaction
                         if isinstance(action_reaction, dict) else {})
            if hasattr(action_reaction, "actions"):
                for a in action_reaction.actions:
                    k = getattr(a, "kind", "unknown")
                    action_kinds[k] = action_kinds.get(k, 0) + 1
            if hasattr(action_reaction, "reactions"):
                for r in action_reaction.reactions:
                    v = getattr(r, "valence", "unknown")
                    reaction_valences[v] = reaction_valences.get(v, 0) + 1
            consequence_profile = {
                "count": ar_status.get("consequence_trace_count", 0)}
            habit_profile = {
                "candidate": ar_status.get("habit_candidate_count", 0),
                "strengthened": ar_status.get("strengthened_habit_count", 0)}
            inhibition_profile = {
                "count": ar_status.get("inhibition_count", 0)}
            no_effect_profile = {
                "count": ar_status.get("no_effect_action_count", 0)}
            policy_profile = {
                "updates": ar_status.get("action_policy_update_count", 0)}

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
            uncertainty_profile=round(pressures.get("uncertainty", 0.0), 4),
            concept_family_distribution=concept_families,
            concept_stability_profile=stability_profile,
            concept_decay_profile=decay_profile,
            concept_relation_profile=relation_profile,
            human_label_concept_contamination=ont_contamination,
            modality_native_concept_ratio=ont_native_ratio,
            sign_family_distribution=sign_families,
            modality_native_sign_ratio=sign_native_ratio,
            cross_modal_sign_ratio=sign_cross_modal_ratio,
            absence_sign_ratio=sign_absence_ratio,
            contaminated_sign_ratio=sign_contaminated_ratio,
            private_syntax_density=syntax_density,
            gloss_dependence_score=gloss_dependence,
            cognitive_move_distribution=move_distribution,
            prediction_profile=prediction_profile,
            failed_prediction_profile=failed_prediction_profile,
            question_pressure_profile=question_pressure_profile,
            simulation_profile=simulation_profile,
            analogy_profile=analogy_profile,
            synthesis_profile=synthesis_profile,
            boundary_clarity_score=boundary_clarity,
            simulation_boundary_integrity=sim_integrity,
            source_attribution_quality=source_quality,
            perspective_shift_profile=perspective_profile,
            receptor_body_schema_stability=body_stability,
            continuity_break_count=continuity_breaks,
            identity_trace_density=identity_density,
            valence_profile=valence_profile,
            push_profile=push_profile,
            desire_kind_distribution=desire_kinds,
            internal_action_profile=internal_action_profile,
            no_op_profile=no_op_profile,
            conflict_profile=conflict_profile,
            blocked_desire_count=blocked_desires,
            desire_outcome_utility=desire_utility,
            action_kind_distribution=action_kinds,
            reaction_valence_distribution=reaction_valences,
            consequence_trace_profile=consequence_profile,
            habit_profile=habit_profile,
            inhibition_profile=inhibition_profile,
            no_effect_action_profile=no_effect_profile,
            learned_policy_profile=policy_profile)


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
