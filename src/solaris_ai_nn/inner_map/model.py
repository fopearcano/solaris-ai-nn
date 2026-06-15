"""Inner MAP data model -- the structured self-model of the NN substrate.

This is the heart of Solaris-AI-NN's self-observation layer. It mirrors
Solaris_Ai's Inner MAP concept (``modules/inner_map.py``): a running, inspectable
model of *what the system currently is*. It makes **no** claim of consciousness;
every field is a concrete, measured property of the substrate, its memory, its
plasticity, its continuity, its boundaries, and its unknowns.

All types are plain dataclasses (stdlib only). The top-level
:class:`InnerMapModel` aggregates the section sub-models and round-trips to/from
JSON via ``to_dict`` / ``from_dict`` (see ``inner_map/serialization.py``).
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ModuleState:
    """A single observed module in the substrate (the 'what exists' answer)."""

    name: str
    role: str = ""
    status: str = "active"
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContinuityState:
    """Runtime continuity (section B): is it alive, and how has it persisted?"""

    alive: bool = True
    lifecycle_state: str = "unknown"
    lifetime_steps: int = 0
    session_steps: int = 0
    restart_count: int = 0
    last_heartbeat_ts: float = 0.0
    last_checkpoint_ts: float = 0.0
    brain_death_gap_seconds: float = 0.0
    graceful_previous_shutdown: bool = True


@dataclass
class NeuralSubstrateState:
    """Neural substrate metrics (section C).

    The "nervous layer" may be any registered substrate (ESN, liquid-state,
    spiking-recurrent); the ``reservoir_*`` names are kept for continuity and
    refer to the active substrate.
    """

    reservoir_size: int = 0
    reservoir_state_norm: float = 0.0
    reservoir_sparsity: float = 0.0
    input_vector_size: int = 0
    readout_output_size: int = 0
    readout_weight_norm: float = 0.0
    prediction_confidence: float = 0.0
    average_prediction_error: float = 0.0
    # Substrate-laboratory observations (Prompt 6).
    substrate_type: str = "esn"
    substrate_activity_rate: float = 0.0
    substrate_drift: float = 0.0
    spike_rate: Optional[float] = None
    silence_ratio: Optional[float] = None
    saturation_ratio: Optional[float] = None
    substrate_switch_history: List[Dict[str, Any]] = field(default_factory=list)
    substrate_comparison: Optional[Dict[str, Any]] = None


@dataclass
class MemoryState:
    """Memory observations (section D)."""

    trace_length: int = 0
    last_signal_types: List[str] = field(default_factory=list)
    dominant_recent_signal_type: Optional[str] = None
    recent_absence_count: int = 0
    recent_reaction_count: int = 0
    consolidated_summaries: List[str] = field(default_factory=list)


@dataclass
class PlasticityState:
    """Habit + synthesis observations (sections E and F) + controlled plasticity."""

    # Habit
    habit_pathways: int = 0
    strongest_habits: List[Dict[str, Any]] = field(default_factory=list)
    most_repeated_mappings: List[Dict[str, Any]] = field(default_factory=list)
    habit_reinforcement_count: int = 0
    # Synthesis
    pruning_count: int = 0
    last_pruning_report: Optional[Dict[str, Any]] = None
    removed_pathway_count: int = 0
    subtraction_ratio: float = 0.0
    # Controlled self-modification (Prompt 5)
    applied_plasticity_count: int = 0
    rejected_plasticity_count: int = 0
    rollback_count: int = 0
    last_applied_step: Optional[Dict[str, Any]] = None
    last_rejected_step: Optional[Dict[str, Any]] = None
    mutable_parameters: Dict[str, Any] = field(default_factory=dict)
    plasticity_safety_status: str = "disabled"
    plasticity_audit_path: Optional[str] = None


@dataclass
class BoundaryState:
    """Observed operational boundaries (section G)."""

    max_reservoir_size: int = 0
    max_trace_length: int = 0
    max_runtime_duration: Optional[float] = None
    max_steps: Optional[int] = None
    continuous_mode_allowed: bool = False
    cpu_only: bool = True
    no_heavy_ml_frameworks: bool = True
    action_authority_suggest_only: bool = True


@dataclass
class TendencyState:
    """Current behavioural tendencies (section H). Suggestions, not decisions."""

    suggested_desire: Optional[str] = None
    suggested_action: Optional[str] = None
    action_tendency_vector: Optional[List[float]] = None
    exploration_tendency: float = 0.0
    stabilization_tendency: float = 0.0
    logos_modulation_influence: Optional[Dict[str, Any]] = None


@dataclass
class UnknownState:
    """Unknown / drift estimates (section I).

    ``unknown_pressure`` is a Mysterium-compatible placeholder: a [0,1]-ish
    scalar standing in for Solaris_Ai's "unknown pressure" until a dedicated
    module exists.
    """

    state_drift_score: float = 0.0
    novelty_estimate: float = 0.0
    unexplained_error_estimate: float = 0.0
    unknown_pressure: float = 0.0


@dataclass
class InnerMapModel:
    """The complete self-model: identity (A) + all observed sections."""

    # A. Identity
    system_name: str = "solaris-ai-nn"
    version: str = "0.1.0"
    run_id: str = ""
    session_id: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    # Sections B-I + module inventory.
    continuity: ContinuityState = field(default_factory=ContinuityState)
    neural: NeuralSubstrateState = field(default_factory=NeuralSubstrateState)
    memory: MemoryState = field(default_factory=MemoryState)
    plasticity: PlasticityState = field(default_factory=PlasticityState)
    boundaries: BoundaryState = field(default_factory=BoundaryState)
    tendencies: TendencyState = field(default_factory=TendencyState)
    unknown: UnknownState = field(default_factory=UnknownState)
    modules: List[ModuleState] = field(default_factory=list)
    # Solaris sidecar integration status (Prompt 7); None when no sidecar.
    # Keys: attached, observing, observe_only, compatibility_level,
    # mirrored_signals, suggestions_produced/published,
    # last_suggestion_confidence, action_authority (always False),
    # substrate_type, sidecar_health.
    integration: Optional[Dict[str, Any]] = None
    # Embodiment status (Prompt 8); None when no simulated body exists.
    # Keys: body, body_type, environment_type, position, energy, exhausted,
    # available/forbidden_actions, last_stimulus_types, last_action,
    # last_action_result, last_reaction_valence, environment_boundaries,
    # nearby_objects, action_authority ("simulation-only"), safety_status.
    embodiment: Optional[Dict[str, Any]] = None
    # Internal language layer status (Prompt 9); None when language is off.
    # Keys: enabled, meaning_atom_count, causal_trace_count,
    # last_explanation_summary, dominant_categories, unknown_statements,
    # queryable, last_session_report_path.
    language: Optional[Dict[str, Any]] = None
    # Evaluation/benchmark status (Prompt 10); None until a benchmark ran.
    # Keys: last_run_id, last_scores, last_failure_findings,
    # reproducibility_status, comparison_summary, artifact_paths.
    evaluation: Optional[Dict[str, Any]] = None
    # Operations status (Prompt 11); None when unsupervised.
    # Keys: run_mode, health_level, watchdog_stop_requested, budget_within,
    # incident_count, last_incident, graceful_shutdown_requested,
    # artifact_rotation, local_status_server, soak_stage.
    operations: Optional[Dict[str, Any]] = None
    # Governance status (Prompt 12); None when ungoverned.
    # Keys: enabled, policy_status, risk_level, active_permissions,
    # approval_count, pending_approval_count, expired_approval_count,
    # emergency_stop_available, emergency_stop_requested,
    # policy_violation_count, last_policy_violation, governance_audit_path,
    # operator_session, runbook_path, claim_guard_status.
    governance: Optional[Dict[str, Any]] = None
    # Pilot-0 deployment status (Prompt 13); None outside a pilot.
    # Keys: pilot_mode_active, pilot_profile, pilot_readiness_status,
    # input_source_count, stream_ingestion_count, pilot_safety_status,
    # pilot_incident_count, pilot_recommendation, pilot_report_path.
    pilot: Optional[Dict[str, Any]] = None
    # Latent cognition status (Prompt 14); None when latent is disabled.
    # Keys: enabled, mode, last_transition, sleep_cycle_count,
    # dream_cycle_count, replay_count, counterfactual_count,
    # anticipation_accuracy, mysterium_pressure, mysterium_reasons,
    # complexity_pressure, consolidated_schema_count, latent_safety_status,
    # latent_report_path.
    latent: Optional[Dict[str, Any]] = None
    # World model status (Prompt 15); None when the world model is disabled.
    # Keys: enabled, graph_node_count, graph_edge_count,
    # strongest_association, top_causal_candidate, unknown_node_count,
    # high_mysterium_areas, context_state, prediction_accuracy,
    # last_pruning_proposal, evidence_ratio, world_model_report_path.
    world_model: Optional[Dict[str, Any]] = None
    # Homeostasis status (Prompt 16); None when homeostasis is disabled.
    # Keys: enabled, dominant_need, dominant_drive, current_valence,
    # valence_trend, being_pressure, not_being_pressure,
    # auto_determination_tension, action_implication, conflict_count,
    # suppressed_desire_count, last_desire_candidates,
    # homeostasis_report_path.
    homeostasis: Optional[Dict[str, Any]] = None
    # Executive status (Prompt 17); None when the executive is disabled.
    # Keys: enabled, mode, active_focus, desire_queue_length,
    # candidate_count, inhibited_candidate_count,
    # selected_action_suggestion, selected_plan_length,
    # no_safe_action_count, last_arbitration_score,
    # last_prospection_confidence, decision_trace_path,
    # executive_report_path.
    executive: Optional[Dict[str, Any]] = None
    # Ego/self-model status (Prompt 18); None when the ego layer is
    # disabled. Keys: enabled, identity_continuity, identity_confidence,
    # identity_warnings, perspective, boundary_violation_count,
    # active_boundaries, violated_boundaries, classification_counts,
    # attribution_unknown_rate, action_authority, self_model_confidence,
    # perspective_shift_count, narrative_trace_path, self_report_path.
    ego: Optional[Dict[str, Any]] = None
    # Communication status (Prompt 19); None when the gateway is absent.
    # Keys: enabled, operator_session_id, dialogue_mode, last_input_kind,
    # unsafe_request_count, pending_confirmation_count,
    # pending_approval_count, transcript_path, last_response_summary,
    # safety_status, plus the gateway counters.
    communication: Optional[Dict[str, Any]] = None
    # Developmental status (Prompt 21); None when the runtime is absent.
    # Keys: enabled, current_epoch, developmental_age_hours,
    # memory_layers, fossil_memory_count, milestone_count,
    # last_milestone, growth_status, drift_status,
    # structural_change_score, phase_transition_candidates,
    # developmental_report_path.
    developmental: Optional[Dict[str, Any]] = None
    # Proto-language status (Prompt 22); None when the layer is absent.
    # Keys: enabled, symbol_count, stable_symbol_count,
    # ambiguous_symbol_count, sequence_count, proto_syntax_rule_count,
    # compression_utility, prediction_utility, first_stable_symbol,
    # latest_proto_utterance, proto_language_report_path, authority.
    proto_language: Optional[Dict[str, Any]] = None
    # Stimulus ecology status (Prompt 23); None when no nursery is
    # attached. Keys: enabled, nursery_id, current_regime,
    # current_cycle_phase, current_season, ecology_event_count,
    # absence_window_count, novelty_count, anomaly_count,
    # delayed_consequence_group_count, seasonal_shift_count,
    # ecology_report_path, authority.
    ecology: Optional[Dict[str, Any]] = None
    # Active perception status (Prompt 24); None when sampling is off.
    # Keys: enabled, sampling_policy_mode, current_attention_focus,
    # top_salience_target, top_uncertainty_target, curiosity_pressure,
    # latest_sampling_action, latest_sampling_result, useful_sampling_rate,
    # blocked_sampling_count, stagnation_state,
    # active_perception_report_path, authority.
    active_perception: Optional[Dict[str, Any]] = None
    # Hypothesis engine status (Prompt 25); None when the engine is off.
    # Keys: enabled, hypothesis_count, highest_priority_hypothesis,
    # current_test_scope, supported_count, falsified_count,
    # inconclusive_count, unsafe_to_test_count, long_lived_unknown_count,
    # last_evidence_result, hypothesis_report_path, authority.
    hypothesis: Optional[Dict[str, Any]] = None
    # Auto-regeneration status (Prompt 26); None when self-repair is off.
    # Keys: enabled, repair_policy_mode, latest_degradation_severity,
    # latest_degradation_type, proposed_repair_count, applied_repair_count,
    # refused_repair_count, rollback_count, quarantine_count,
    # last_repair_report_path, authority.
    autoregeneration: Optional[Dict[str, Any]] = None
    # LOGOS complexity status (Prompt 27); None when LOGOS is off.
    # Keys: enabled, complexity_band, complexity_pressure,
    # active_tension_count, unresolved_tension_count, latest_tension,
    # latest_synthesis_candidate, applied_synthesis_count,
    # preserved_tension_count, esc_triggered, logos_report_path, authority.
    logos: Optional[Dict[str, Any]] = None
    # Conscience runtime status (Prompt 28); None when the orchestrator is
    # not running. Keys mirror ConscienceOrchestrator.summary(): run_id,
    # profile, mode, authority, current_spine_phase, step_count,
    # enabled_modules, missing_modules, degraded_modules, bus_message_count,
    # scheduler_skip_count, stopped, authority_note. The orchestrator owns no
    # action authority and no module is sovereign.
    conscience: Optional[Dict[str, Any]] = None
    # Pilot-1 month-scale soak status (Prompt 29); None when no pilot is
    # active. Keys: pilot1_enabled, pilot_mode, pilot_phase,
    # elapsed_pilot_seconds, uptime_ratio, daily_report_count,
    # weekly_report_count, latest_failure_mode, exit_recommendation,
    # dashboard_path, pilot_report_path. Operational status only; a pilot is
    # a bounded software test, never evidence of consciousness.
    pilot1: Optional[Dict[str, Any]] = None
    # Post-pilot forensic analysis status (Prompt 30); None when no analysis
    # has run. Keys: post_pilot_analysis_available, artifact_completeness,
    # growth_classification, structural_evidence_count, regression_severity,
    # traceability_score, reproducibility_score, phase2_recommendation,
    # post_pilot_report_path, research_dossier_path. Analyzability/operational
    # findings only; never a consciousness claim.
    post_pilot: Optional[Dict[str, Any]] = None
    # Read-only sensory membrane status (Prompt 31); None when the membrane is
    # off. Keys: enabled, source_count, active_source_count,
    # event_count_by_modality, latest_event_timestamp, dropped_events,
    # malformed_events, provenance_completeness, read_only, report_path. The
    # membrane is read-only; environmental input is never an operator command.
    sensory_membrane: Optional[Dict[str, Any]] = None
    # Pilot-2 read-only environmental soak status (Prompt 32); None when no
    # Pilot-2 is active. Keys: pilot2_enabled, pilot2_phase, source_mode,
    # source_count, reliable_source_count, unsafe_source_count,
    # grounding_quality, comparison_arm_active, daily/weekly review paths,
    # report path, recommendation. Read-only; the system never acts on the
    # environment, and no consciousness is claimed.
    pilot2: Optional[Dict[str, Any]] = None
    # Pilot-3 motor membrane status (Prompt 33); None when the membrane is
    # off. Keys: enabled, embodiment profile, real_world_authority=false,
    # action/simulated/dry-run/veto/blocked-real-world counts, latest motor
    # action, latest firewall decision, action ledger path, report path.
    # Simulated/dry-run only; the system never acts on the real world.
    motor_membrane: Optional[Dict[str, Any]] = None
    # Pilot-3 simulated embodiment soak status (Prompt 34); None when the soak
    # is off. Keys: pilot3_soak_enabled, pilot3_soak_phase,
    # embodiment_condition, simulated/dry-run/veto counts, firewall_audit_status,
    # latest_action_grounding_quality, sandbox_overfit_warning,
    # latest_pilot3_report_path, recommendation. Simulation/dry-run only; the
    # system never acts on the real world.
    pilot3: Optional[Dict[str, Any]] = None
    # Pilot-4 planning-only readiness status (Prompt 35); None when planning is
    # off. Keys: pilot4_planning_enabled, current_planning_phase,
    # real_world_actuation_enabled=false, actuator_taxonomy_status,
    # forbidden_actuator_count, risk_assessment_status, consent_boundary_status,
    # threat_model_status, readiness_conclusion, pilot4_dossier_path. Planning
    # only; the system enables no actuation.
    pilot4: Optional[Dict[str, Any]] = None
    # System-wide safety invariant status (Prompt 36); None when the safety
    # runner is not attached. Keys: safety_invariant_status, latest_fast_check,
    # latest_full_check, red_team_summary, critical_failure_count,
    # assurance_case_status, unresolved_safety_blocker_count,
    # safety_dashboard_path. Read-only/inert; the safety layer runs no actions.
    safety_invariants: Optional[Dict[str, Any]] = None
    # Research-lab status (Prompt 37); None when the lab is not attached. Keys:
    # research_lab_enabled, current_experiment, variants/baselines/ablations
    # tested, best_variant_by_metric_group, harmful_module_candidates,
    # inconclusive_module_candidates, latest_research_report_path. The lab is a
    # bounded measurement instrument; it holds no external authority.
    research_lab: Optional[Dict[str, Any]] = None
    # Architecture-evolution status (Prompt 38); None when not attached. Keys:
    # architecture_evolution_enabled, module_inventory_count,
    # module_lifecycle_summary, design_debt_count, open_adr_count,
    # latest_architecture_snapshot/review/roadmap, pruning/promotion proposal
    # counts. Planning-only; the layer modifies no source code.
    architecture_evolution: Optional[Dict[str, Any]] = None
    # Operator-console status (Prompt 39); None when not attached. Keys:
    # operator_console_enabled, available_profile_count, blocked_profile_count,
    # latest_status_board_path, latest_decision_board_path, latest_next_action,
    # latest_approval_record, latest_export_bundle, last_blocked_run. The console
    # is a local file-backed coordinator; it holds no real-world authority and
    # cannot bypass governance or safety.
    operator_console: Optional[Dict[str, Any]] = None
    # Plural-sensorium status (Prompt 41); None when not attached. Keys:
    # plural_sensorium_enabled, active_modality_count, active_receptor_count,
    # sensory_field_pressure, absence_pressure, novelty_pressure,
    # rhythm_pressure, cross_modal_pressure, receptor_adaptation_count,
    # baseline_shift_count, invariant_candidate_count,
    # modality_grounded_proto_symbol_count, cross_modal_relation_count,
    # human_label_contamination_score, latest_plural_sensorium_report_path. The
    # sensorium is read-only; it controls no hardware and holds no authority.
    plural_sensorium: Optional[Dict[str, Any]] = None
    # Minimal-field-organism demo status (Prompt 42); None when not attached.
    # Keys: organismic_demo_enabled, latest_demo_run_id, active_feeder_count,
    # active_receptor_count, changed_perception_score, cross_modal_relation_count,
    # proto_symbol_candidate_count, latest_report_path,
    # latest_negative_result_count. The demo is a bounded, read-only observation.
    organismic_demo: Optional[Dict[str, Any]] = None
    # Live-field status (Prompt 43); None when not attached. Keys:
    # live_field_enabled, live_mode_allowed, feeder_count, active_source_count,
    # silent_source_count, corrupt_source_count, active_modality_count,
    # live_field_pressure, live_absence_pressure, live_baseline_shift_count,
    # changed_perception_score, latest_live_field_report_path. The live field
    # reads external feeders only; it controls no hardware and mutates no source.
    live_field: Optional[Dict[str, Any]] = None
    # Sensorium-lab status (Prompt 44); None when not attached. Keys:
    # sensorium_lab_enabled, latest_study_id, world_signature_count,
    # modality_fingerprint_count, strongest_structural_difference,
    # inconclusive_comparison_count, human_label_contamination_score,
    # latest_differentiation_report_path. The lab compares observable internal
    # structures only; it makes no claim of subjective experience.
    sensorium_lab: Optional[Dict[str, Any]] = None
    # Feeder-SDK status (Prompt 45); None when not attached. Keys:
    # feeder_sdk_enabled, feeder_pack_manifest_path, available_feeder_count,
    # active_feeder_output_count, invalid_feeder_event_count,
    # feeder_privacy_warning_count, feeder_safety_warning_count,
    # latest_feeder_monitor_snapshot_path. Feeders are outside Solaris; Solaris
    # reads their output read-only and controls nothing.
    feeder_sdk: Optional[Dict[str, Any]] = None
    # Perceptual-metabolism status (Prompt 46); None when not attached. Keys:
    # perceptual_metabolism_enabled, perceptual_need_count,
    # dominant_perceptual_need, overload_state, deprivation_state,
    # source_diet_diversity, attention_allocation_state,
    # consolidation_pressure_score, latest_metabolism_report_path. Needs are
    # operational pressures, not feelings; regulation is internal and bounded.
    perceptual_metabolism: Optional[Dict[str, Any]] = None
    # Perceptual-ontogenesis status (Prompt 47); None when not attached. Keys:
    # perceptual_ontogenesis_enabled, perceptual_atom_count, proto_concept_count,
    # stable_concept_count, decaying_concept_count, concept_family_count,
    # concept_relation_count, human_label_contamination_score,
    # world_formation_density, latest_ontogenesis_report_path. Proto-concepts are
    # operational structures, not words; world formation is structural, not
    # subjective experience.
    perceptual_ontogenesis: Optional[Dict[str, Any]] = None
    # Semiogenesis status (Prompt 48); None when not attached. Keys:
    # semiogenesis_enabled, internal_sign_count, stable_sign_count,
    # sign_family_count, private_syntax_pattern_count, internal_utterance_count,
    # sign_drift_count, contaminated_sign_ratio, gloss_dependence_score,
    # latest_semiogenesis_report_path. Signs are operational markers, not human
    # words; private syntax is internal relation structure, not human grammar.
    semiogenesis: Optional[Dict[str, Any]] = None
    # Sensorium-cognition status (Prompt 49); None when not attached. Keys:
    # sensorium_cognition_enabled, cognitive_move_count, prediction_count,
    # failed_prediction_count, question_pressure_count, internal_simulation_count,
    # counterfactual_count, synthesis_count, unresolved_tension_count,
    # latest_cognition_report_path. Cognitive moves are operations over signs/
    # concepts, not human-language thought; simulation is not real observation.
    sensorium_cognition: Optional[Dict[str, Any]] = None
    # Self-boundary status (Prompt 50); None when not attached. Keys:
    # self_boundary_enabled, boundary_confidence_score, current_perspective_frame,
    # receptor_body_schema_count, continuity_anchor_count, continuity_break_count,
    # source_attribution_uncertainty_score, simulation_boundary_warning_count,
    # identity_trace_event_count, latest_self_boundary_report_path. Self-boundary
    # is operational, not subjective selfhood; body schema is receptor structure.
    self_boundary: Optional[Dict[str, Any]] = None
    # Desire-formation status (Prompt 51); None when not attached. Keys:
    # desire_formation_enabled, valence_gradient_count, push_count,
    # desire_candidate_count, active_desire_count, inhibited_desire_count,
    # deferred_desire_count, internal_action_count, no_op_count,
    # safety_blocked_desire_count, motivation_field, latest_desire_formation_
    # report_path. Desire is operational pressure toward internal action, not
    # emotion, free will, or agency.
    desire_formation: Optional[Dict[str, Any]] = None
    # Action-reaction status (Prompt 52); None when not attached. Keys:
    # action_reaction_enabled, selected_action_count, blocked_action_count,
    # no_op_count, reaction_count, consequence_trace_count, learned_effect_count,
    # habit_candidate_count, inhibition_count, action_policy_update_count,
    # latest_action_reaction_report_path. Actions are internal/simulated/
    # report-only; no real-world actuation; not agency or free will.
    action_reaction: Optional[Dict[str, Any]] = None
    # Developmental-life status (Prompt 53); None when not attached. Keys:
    # developmental_life_enabled, current_life_cycle_phase,
    # developmental_epoch_count, maturation_marker_count,
    # phase_transition_count, plateau_count, regression_count,
    # structural_growth_status, latest_developmental_report_path. Life cycle is
    # operational runtime structure, not biological life; growth is structural
    # change, not proof of intelligence.
    developmental_life: Optional[Dict[str, Any]] = None
    # Developmental-soak status (Prompt 54); None when not attached. Keys:
    # developmental_soak_enabled, active_plan_id, current_stage,
    # preflight_passed, checkpoint_count, daily_packet_count,
    # weekly_review_count, restart_drill_count, control_arm_count,
    # evidence_claim_count, autopsy_recommendation, soak_safety_block_count,
    # latest_soak_report_path. The soak protocol studies structural
    # development; it is not biological life, consciousness, or agency.
    developmental_soak: Optional[Dict[str, Any]] = None

    def touch(self) -> None:
        """Mark the model as freshly updated."""
        self.updated_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Recursively serialise to a JSON-friendly dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InnerMapModel":
        """Rebuild a model (with nested sub-models) from a dict."""
        data = dict(data)
        nested = {
            "continuity": ContinuityState,
            "neural": NeuralSubstrateState,
            "memory": MemoryState,
            "plasticity": PlasticityState,
            "boundaries": BoundaryState,
            "tendencies": TendencyState,
            "unknown": UnknownState,
        }
        kwargs: Dict[str, Any] = {}
        valid = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        for key, value in data.items():
            if key not in valid:
                continue
            if key in nested and isinstance(value, dict):
                sub = nested[key]
                sub_valid = set(sub.__dataclass_fields__)  # type: ignore[attr-defined]
                kwargs[key] = sub(**{k: v for k, v in value.items() if k in sub_valid})
            elif key == "modules" and isinstance(value, list):
                kwargs[key] = [
                    ModuleState(**{k: v for k, v in m.items()
                                   if k in ModuleState.__dataclass_fields__})  # type: ignore[attr-defined]
                    for m in value
                ]
            else:
                kwargs[key] = value
        return cls(**kwargs)
