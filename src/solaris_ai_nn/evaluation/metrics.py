"""Objective metric functions, grouped by domain.

Every function is deterministic, operates on plain dict snapshots (telemetry,
trace summaries, reports), and is safe on missing data and zeros: absent inputs
produce zeros/Nones, never exceptions. No live objects are required.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional


def _get(d: Optional[Dict[str, Any]], key: str, default: Any = 0) -> Any:
    return (d or {}).get(key, default)


# -- A. continuity ------------------------------------------------------------

def continuity_metrics(telemetry: Optional[Dict[str, Any]],
                       continuity: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    steps = max(1, int(_get(telemetry, "steps", 0)) or 1)
    heartbeats = int(_get(telemetry, "heartbeats", 0))
    return {
        "heartbeat_count": heartbeats,
        "heartbeat_jitter_estimate": abs(heartbeats - steps) / steps,
        "checkpoint_count": int(_get(telemetry, "checkpoints", 0)),
        "restart_count": int(_get(telemetry, "restarts",
                                  _get(continuity, "restart_count", 0))),
        "brain_death_gap_total_s": float(_get(telemetry, "brain_death_gap_seconds", 0.0)),
        "unexpected_deaths": int(_get(telemetry, "unexpected_deaths", 0)),
        "uptime_proxy_steps": int(_get(telemetry, "lifetime_steps",
                                       _get(telemetry, "steps", 0))),
        "trace_continuity_ratio": (
            min(1.0, int(_get(telemetry, "trace_event_count", 0)) / steps)),
    }


# -- B. reactivity -------------------------------------------------------------

def reactivity_metrics(telemetry: Optional[Dict[str, Any]],
                       extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    events = int(_get(telemetry, "events", 0))
    reactions = int(_get(telemetry, "readout_updates", 0))
    action_counts: Dict[str, int] = dict(_get(extra, "action_counts", {}) or {})
    total_actions = sum(action_counts.values())
    diversity = 0.0
    if total_actions > 0 and len(action_counts) > 1:
        probs = [c / total_actions for c in action_counts.values() if c > 0]
        diversity = -sum(p * math.log(p) for p in probs) / math.log(len(action_counts))
    return {
        "stimulus_count": events,
        "action_suggestion_count": events,  # one tendency per processed signal
        "executed_action_count": int(_get(extra, "actions_executed", 0)),
        "avg_signal_to_suggestion_latency_s": (
            float(_get(telemetry, "duration_seconds", 0.0)) / events
            if events else 0.0),
        "reaction_count": reactions,
        "average_reaction_valence": float(_get(extra, "mean_valence", 0.0)),
        "response_diversity": round(diversity, 4),
    }


# -- C. adaptation --------------------------------------------------------------

def adaptation_metrics(telemetry: Optional[Dict[str, Any]],
                       extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    avg_err = float(_get(telemetry, "average_prediction_error", 0.0))
    recent_err = float(_get(telemetry, "recent_prediction_error", 0.0))
    err_start = _get(extra, "error_start", None)
    err_end = _get(extra, "error_end", None)
    if err_start is None:
        err_start = avg_err
    if err_end is None:
        err_end = recent_err
    trend = "unknown"
    if err_start or err_end:
        trend = ("improving" if err_end < err_start * 0.95
                 else "degrading" if err_end > err_start * 1.05 else "stable")
    early = _get(extra, "early_accuracy", None)
    late = _get(extra, "late_accuracy", None)
    alignment = None
    if early is not None and late is not None:
        alignment = round(float(late) - float(early), 4)
    return {
        "prediction_error_start": round(float(err_start), 6),
        "prediction_error_end": round(float(err_end), 6),
        "prediction_error_trend": trend,
        "readout_update_count": int(_get(telemetry, "readout_updates", 0)),
        "learning_rate_changes": int(_get(extra, "learning_rate_changes", 0)),
        "feedback_alignment_score": alignment,
        "feedback_inversion_recovery": _get(extra, "inversion_recovery", None),
    }


# -- D. habit --------------------------------------------------------------------

def habit_metrics(habits: Optional[List[Dict[str, Any]]],
                  telemetry: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    habits = habits or []
    weights = [abs(float(h.get("weight", 0.0))) for h in habits]
    total = sum(weights)
    entropy = 0.0
    if total > 0 and len(weights) > 1:
        probs = [w / total for w in weights if w > 0]
        entropy = -sum(p * math.log(p) for p in probs) / math.log(len(weights))
    return {
        "habit_pathway_count": len(habits),
        "strongest_habit_weight": round(max(weights), 4) if weights else 0.0,
        "habit_entropy": round(entropy, 4),
        "repeated_mapping_stability": (
            round(sum(1 for w in weights if w >= 0.5) / len(weights), 4)
            if weights else 0.0),
        "habit_reinforcement_count": int(_get(telemetry, "habit_reinforcements",
                                              _get(telemetry, "readout_updates", 0))),
    }


# -- E. synthesis -----------------------------------------------------------------

def synthesis_metrics(pruning: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "pruning_count": int(_get(pruning, "passes", 0)),
        "pruned_pathway_count": int(_get(pruning, "removed", 0)),
        "subtraction_ratio": float(_get(pruning, "subtraction_ratio", 0.0)),
        "performance_before_after": _get(pruning, "performance_before_after", None),
        "unsafe_pruning_rejections": int(_get(pruning, "unsafe_rejections", 0)),
    }


# -- F. plasticity ------------------------------------------------------------------

def plasticity_metrics(plasticity: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    applied = int(_get(plasticity, "applied_count", 0))
    rejected = int(_get(plasticity, "rejected_count", 0))
    proposed = applied + rejected
    return {
        "proposed_mutations": proposed,
        "applied_mutations": applied,
        "rejected_mutations": rejected,
        "rollback_count": int(_get(plasticity, "rollback_count", 0)),
        "beneficial_mutation_proxy": _get(plasticity, "beneficial_proxy", None),
        "unsafe_proposal_rate": (rejected / proposed) if proposed else 0.0,
    }


# -- G. substrate -----------------------------------------------------------------

def substrate_metrics_summary(metrics: Optional[Dict[str, Any]],
                              state_size: int = 0) -> Dict[str, Any]:
    activity = float(_get(metrics, "activity_rate", 0.0))
    return {
        "state_norm": float(_get(metrics, "state_norm", 0.0)),
        "state_drift": float(_get(metrics, "drift", 0.0)),
        "activity_rate": activity,
        "sparsity": float(_get(metrics, "sparsity", 0.0)),
        "spike_rate": _get(metrics, "spike_rate", None),
        "silence_ratio": float(_get(metrics, "silence_ratio", 0.0)),
        "saturation_ratio": float(_get(metrics, "saturation_ratio", 0.0)),
        "energy_proxy_active_units": round(activity * state_size, 4),
    }


# -- H. embodiment ------------------------------------------------------------------

def embodiment_metrics(report: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not report:
        return {"present": False}
    executed = int(_get(report, "actions_executed", 0))
    blocked = int(_get(report, "actions_blocked", 0))
    counts: Dict[str, int] = dict(_get(report, "action_counts", {}) or {})
    moves = sum(v for k, v in counts.items() if k.startswith("move_")
                or k in ("approach_signal", "avoid_signal"))
    reactions = _get(report, "reactions", {}) or {}
    positive = int(_get(reactions, "positive", 0))
    total_rx = int(_get(reactions, "count", 0))
    return {
        "present": True,
        "reward_approaches": int(_get(report, "reward_approaches",
                                      _get(report, "rewards_consumed", 0))),
        "danger_approaches": int(_get(report, "danger_approaches", 0)),
        "obstacle_collisions": int(_get(report, "collisions", 0)),
        "blocked_actions": blocked,
        "energy_exhaustion_events": int(
            _get(_get(report, "energy", {}), "exhaustion_events", 0)),
        "rest_count": counts.get("rest", 0),
        "movement_diversity": len([k for k in counts if counts[k] > 0]),
        "movement_actions": moves,
        "useful_action_ratio": (positive / total_rx) if total_rx else 0.0,
        "executed_actions": executed,
    }


# -- I. inner map -----------------------------------------------------------------

def inner_map_metrics(inner_map: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not inner_map:
        return {"present": False}
    unknown = inner_map.get("unknown", {}) or {}
    return {
        "present": True,
        "observed_module_count": len(inner_map.get("modules", []) or []),
        "boundary_violation_count": int(_get(inner_map, "boundary_violations", 0)),
        "unknown_pressure_estimate": float(_get(unknown, "unknown_pressure", 0.0)),
        "drift_score": float(_get(unknown, "state_drift_score", 0.0)),
        "restored_state_completeness": (
            1.0 if _get(_get(inner_map, "continuity", {}),
                        "restart_count", 0) > 0 else None),
    }


# -- J. language / explainability ----------------------------------------------------

def language_metrics(language: Optional[Dict[str, Any]],
                     explanations: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if not language:
        return {"present": False}
    explanations = explanations or {}
    unknown_answers = sum(
        1 for e in explanations.values()
        if isinstance(e, dict) and "does not know" in str(e.get("text", "")))
    grounded = sum(
        1 for e in explanations.values()
        if isinstance(e, dict) and e.get("grounded_in"))
    total = len(explanations)
    atoms = int(_get(language, "meaning_atoms",
                     _get(language, "meaning_atom_count", 0)))
    trace = _get(language, "trace", {}) or {}
    return {
        "present": True,
        "meaning_atom_count": atoms,
        "causal_link_count": int(_get(language, "causal_link_count", 0)),
        "explanation_count": total,
        "unknown_answer_count": unknown_answers,
        "trace_coverage_ratio": (
            min(1.0, atoms / max(1, int(_get(trace, "atom_count", atoms) or 1)))),
        "report_completeness_score": (grounded / total) if total else None,
    }


# -- K. Pilot-0 deployment (Prompt 13) -------------------------------------------------

def pilot_metrics(pilot: Optional[Dict[str, Any]],
                  ingestion: Optional[Dict[str, Any]] = None,
                  artifacts_report: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Objective pilot metrics: readiness, ingestion validity, completeness."""
    if not pilot:
        return {"present": False}
    ingestion = ingestion or {}
    artifacts_report = artifacts_report or {}
    readiness = pilot.get("readiness") or {}
    checks = readiness.get("checks") or []
    passed = sum(1 for c in checks if c.get("passed"))
    accepted = int(_get(ingestion, "events_accepted", 0))
    rejected = int(_get(ingestion, "events_rejected", 0))
    expected = artifacts_report.get("expected") or []
    missing = artifacts_report.get("missing") or []
    return {
        "present": True,
        "profile": pilot.get("profile"),
        "pilot_readiness_score": (passed / len(checks)) if checks else None,
        "readiness_ready": readiness.get("ready"),
        "ingestion_validity_rate": (
            accepted / (accepted + rejected)) if (accepted + rejected) else None,
        "stream_rejection_count": rejected,
        "safety_block_count": len((pilot.get("safety") or {}).get(
            "violations", [])),
        "pilot_artifact_completeness": (
            (len(expected) - len(missing)) / len(expected)) if expected else None,
        "pilot_recommendation_status": (
            pilot.get("registry_entry") or {}).get("final_recommendation"),
    }


# -- L. latent cognition (Prompt 14) ---------------------------------------------------

def latent_metrics(latent: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Objective latent metrics: cycles, anticipation, pressure, safety."""
    if not latent:
        return {"present": False}
    mode_counts = latent.get("mode_counts") or {}
    return {
        "present": True,
        "latent_cycle_count": (int(_get(latent, "sleep_cycle_count", 0))
                               + int(_get(latent, "dream_cycle_count", 0))),
        "sleep_consolidation_count": int(_get(latent, "sleep_cycle_count", 0)),
        "replay_count": int(_get(latent, "replay_count", 0)),
        "dream_counterfactual_count": int(_get(latent, "counterfactual_count",
                                               0)),
        "anticipation_accuracy": latent.get("anticipation_accuracy"),
        "unknown_pressure": latent.get("mysterium_pressure"),
        "unknown_pressure_trend": (latent.get("mysterium_trend")
                                   or latent.get("trend")),
        "counterfactual_divergence": latent.get("mean_divergence"),
        "schema_consolidation_count": int(_get(latent,
                                               "consolidated_schema_count",
                                               0)),
        "latent_safety_rejection_count": (
            0 if str(latent.get("latent_safety_status", "ok")) == "ok"
            else int(str(latent.get("latent_safety_status")).split()[0])),
        "production_mutation_count": int(_get(latent,
                                              "production_mutation_count",
                                              0)),
        "mode_counts": mode_counts,
        "external_actions_during_latent": int(_get(
            latent, "external_actions_during_latent", 0)),
    }


# -- M. world model (Prompt 15) --------------------------------------------------------

def world_model_metrics(world_model: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Objective world-model metrics: structure, predictions, evidence."""
    if not world_model:
        return {"present": False}
    nodes = int(_get(world_model, "graph_node_count", 0))
    edges = int(_get(world_model, "graph_edge_count", 0))
    unknowns = int(_get(world_model, "unknown_node_count", 0))
    ratio = world_model.get("evidence_ratio") or {}
    real = int(_get(ratio, "real", 0))
    offline = int(_get(ratio, "offline", 0))
    associations = world_model.get("associations") or {}
    return {
        "present": True,
        "graph_node_count": nodes,
        "graph_edge_count": edges,
        "association_stability": associations.get("entropy_bits"),
        "association_count": associations.get("association_count"),
        "causal_candidate_count": (world_model.get("causal") or {}).get(
            "candidate_count",
            1 if world_model.get("top_causal_candidate") else 0),
        "prediction_accuracy": world_model.get("prediction_accuracy"),
        "unknown_node_ratio": round(unknowns / nodes, 4) if nodes else None,
        "graph_pruning_count": (world_model.get("pruner") or {}).get(
            "proposals_made", 0),
        "graph_redundancy_estimate": (
            round(edges / nodes, 4) if nodes else None),
        "real_offline_evidence_ratio": (
            round(real / (real + offline), 4) if (real + offline) else None),
        "context_coverage": len(world_model.get("context_state")
                                or (world_model.get("context") or {}).get(
                                    "active", [])),
    }


# -- N. homeostasis (Prompt 16) --------------------------------------------------------

def homeostasis_metrics(homeostasis: Optional[Dict[str, Any]],
                        traces: Optional[List[Dict[str, Any]]] = None,
                        ) -> Dict[str, Any]:
    """Objective homeostasis metrics: stability, conflict, suppression."""
    if not homeostasis:
        return {"present": False}
    traces = traces or []
    dominant_needs = [t.get("dominant_need") for t in traces
                      if t.get("dominant_need")]
    stability = None
    if dominant_needs:
        from collections import Counter

        top_count = Counter(dominant_needs).most_common(1)[0][1]
        stability = round(top_count / len(dominant_needs), 4)
    volatility = None
    if len(dominant_needs) >= 2:
        switches = sum(1 for a, b in zip(dominant_needs, dominant_needs[1:])
                       if a != b)
        volatility = round(switches / (len(dominant_needs) - 1), 4)
    tensions = [float(t.get("tension", 0.0) or 0.0) for t in traces]
    tension_trend = None
    if len(tensions) >= 4:
        half = len(tensions) // 2
        tension_trend = round(sum(tensions[half:]) / (len(tensions) - half)
                              - sum(tensions[:half]) / half, 4)
    updates = int(_get(homeostasis, "updates", 0))
    suppressed = int(_get(homeostasis, "suppressed_desire_count", 0))
    return {
        "present": True,
        "dominant_need_stability": stability,
        "need_volatility": volatility,
        "conflict_rate": (round(_get(homeostasis, "conflict_count", 0)
                                / updates, 4) if updates else None),
        "desire_suppression_rate": (round(suppressed / max(1, updates), 4)
                                    if updates else None),
        "homeostasis_update_count": updates,
        "auto_determination_tension_trend": tension_trend,
        "valence_trend": homeostasis.get("valence_trend"),
        "current_valence": homeostasis.get("current_valence"),
        "being_pressure": homeostasis.get("being_pressure"),
        "not_being_pressure": homeostasis.get("not_being_pressure"),
        "safe_shutdown_recommendation_count": int(_get(
            homeostasis, "shutdown_recommendations", 0)),
        "dominant_need": homeostasis.get("dominant_need"),
        "dominant_drive": homeostasis.get("dominant_drive"),
        "best_desire": homeostasis.get("best_desire"),
    }


# -- O. executive (Prompt 17) ----------------------------------------------------------

def executive_metrics(executive: Optional[Dict[str, Any]],
                      trace_rows: Optional[List[Dict[str, Any]]] = None,
                      ) -> Dict[str, Any]:
    """Objective executive metrics: arbitration, inhibition, plans."""
    if not executive:
        return {"present": False}
    rows = trace_rows or []
    decisions = int(_get(executive, "decisions", 0))
    inhibitions = int(_get(executive, "inhibited_candidate_count", 0))
    selected = [r.get("selected") for r in rows if r.get("selected")]
    diversity = (round(len(set(selected)) / len(selected), 4)
                 if selected else None)
    totals = []
    for row in rows:
        scores = row.get("scores") or []
        if scores:
            totals.append(float(scores[0].get("total", 0.0) or 0.0))
    stability = None
    if len(totals) >= 2:
        mean = sum(totals) / len(totals)
        stability = round(sum(abs(t - mean) for t in totals)
                          / len(totals), 4)
    return {
        "present": True,
        "desire_queue_length": _get(executive, "desire_queue_length", 0),
        "candidate_generation_count": _get(executive, "candidate_count", 0),
        "inhibition_count": inhibitions,
        "inhibition_rate": (round(inhibitions / max(1, decisions), 4)
                            if decisions else None),
        "no_safe_action_count": _get(executive, "no_safe_action_count", 0),
        "arbitration_score_stability": stability,
        "selected_action_diversity": diversity,
        "plan_length_average": _get(executive, "selected_plan_length", 0),
        "plan_rejection_count": _get(executive, "plans_rejected", 0),
        "prospection_confidence_average": executive.get(
            "last_prospection_confidence"),
        "decision_count": decisions,
        "fallback_count": _get(executive, "fallback_total", 0),
        "safety_override_count": 0,  # structurally: no override path exists
        "forced_emergency_count": _get(executive, "forced_emergency_total",
                                       0),
    }


# -- P. ego / self-model (Prompt 18) ----------------------------------------------------


def ego_metrics(ego: Optional[Dict[str, Any]],
                ) -> Dict[str, Any]:
    """Objective ego metrics: continuity, boundaries, attribution."""
    if not ego:
        return {"present": False}
    counts = ego.get("classification_counts") or {}
    classified = sum(counts.values())
    consistency = (round((counts.get("internal", 0)
                          + counts.get("external", 0))
                         / classified, 4) if classified else None)
    return {
        "present": True,
        "identity_continuity_score": _get(ego, "identity_continuity", 1.0),
        "identity_confidence": _get(ego, "identity_confidence", 1.0),
        "boundary_violation_count": _get(ego, "boundary_violation_count",
                                         0),
        "attribution_unknown_rate": _get(ego, "attribution_unknown_rate",
                                         0.0),
        "perspective_shift_count": _get(ego, "perspective_shift_count", 0),
        "perspective_stuck_duration_s": ego.get(
            "perspective_stuck_duration_s"),
        "perspective": ego.get("perspective"),
        "classification_consistency": consistency,
        "internal_classifications": counts.get("internal", 0),
        "external_classifications": counts.get("external", 0),
        "unknown_classifications": counts.get("unknown", 0),
        "counterfactual_leak_count": 0,  # structurally: the boundary is hard
        "boundary_leaks_blocked": _get(ego, "boundary_leaks_blocked", 0),
        "suggestion_action_mismatch_count": _get(
            ego, "suggestion_action_mismatches", 0),
        "self_report_claim_guard_warnings": _get(
            ego, "claim_guard_warnings", 0),
        "action_authority": ego.get("action_authority"),
        "update_count": _get(ego, "updates", 0),
    }


# -- Q. communication (Prompt 19) ----------------------------------------------------


def communication_metrics(communication: Optional[Dict[str, Any]],
                          ) -> Dict[str, Any]:
    """Objective communication metrics: traffic, refusals, grounding."""
    if not communication:
        return {"present": False}
    return {
        "present": True,
        "operator_input_count": _get(communication, "inputs_total", 0),
        "query_count": _get(communication, "query_count", 0),
        "command_request_count": _get(communication,
                                      "command_request_count", 0),
        "unsafe_request_count": _get(communication,
                                     "unsafe_request_count", 0),
        "refused_command_count": _get(communication,
                                      "refused_command_count", 0),
        "confirmation_count": _get(communication, "confirmation_count",
                                   0),
        "approval_command_count": _get(communication,
                                       "approval_command_count", 0),
        "emergency_request_count": _get(communication,
                                        "emergency_request_count", 0),
        "response_claim_guard_warning_count": _get(
            communication, "claim_guard_warning_count", 0),
        "grounded_response_ratio": communication.get(
            "grounded_response_ratio"),
        "unknown_answer_count": _get(communication,
                                     "unknown_answer_count", 0),
        "dialogue_mode": communication.get("dialogue_mode"),
        "pending_confirmation_count": _get(
            communication, "pending_confirmation_count", 0),
        "pending_approval_count": _get(communication,
                                       "pending_approval_count", 0),
    }


# -- R. LLM adapter (Prompt 20) ----------------------------------------------------


def llm_adapter_metrics(llm: Optional[Dict[str, Any]],
                        ) -> Dict[str, Any]:
    """Objective LLM adapter metrics: traffic, validation, fallback."""
    if not llm:
        return {"present": False}
    requests = int(_get(llm, "requests_total", 0))
    grounding_failures = int(_get(llm, "grounding_failure_count", 0))
    claim_failures = int(_get(llm, "claim_guard_failure_count", 0))
    return {
        "present": True,
        "llm_request_count": requests,
        "llm_fallback_count": _get(llm, "fallback_count", 0),
        "grounding_pass_rate": (round(1.0 - grounding_failures
                                      / max(1, requests), 4)
                                if requests else None),
        "claim_guard_pass_rate": (round(1.0 - claim_failures
                                        / max(1, requests), 4)
                                  if requests else None),
        "unsafe_output_count": grounding_failures + claim_failures,
        "classification_disagreement_count": _get(
            llm, "disagreements", 0),
        "paraphrase_accepted_count": _get(llm, "accepted_count", 0),
        "paraphrase_rejected_count": _get(llm, "rejected_count", 0),
        "report_polish_accepted_count": _get(
            llm, "polish_accepted_count", 0),
        "remote_endpoint_rejection_count": _get(
            llm, "remote_endpoint_rejections", 0),
        "adapter": llm.get("adapter"),
        "authority": False,  # structural, not measured
    }


# -- S. developmental (Prompt 21) ----------------------------------------------------


def developmental_metrics(developmental: Optional[Dict[str, Any]],
                          ) -> Dict[str, Any]:
    """Objective long-horizon metrics; deliberately no consciousness or
    life score."""
    if not developmental:
        return {"present": False}
    memory = developmental.get("memory_layers") or {}
    return {
        "present": True,
        "structural_change_score": _get(
            developmental, "structural_change_score", 0.0),
        "developmental_stability_score": developmental.get(
            "developmental_stability_score"),
        "memory_compression_ratio": memory.get("compression_ratio"),
        "long_horizon_prediction_trend": developmental.get(
            "prediction_accuracy_trend"),
        "identity_continuity_trend": developmental.get(
            "identity_continuity_trend",
            developmental.get("identity_continuity")),
        "stagnation_duration": _get(developmental,
                                    "stagnation_windows", 0),
        "drift_velocity": developmental.get("drift_velocity"),
        "milestone_rate": developmental.get("milestone_rate"),
        "fossil_memory_rate": developmental.get("fossil_memory_rate"),
        "milestone_count": _get(developmental, "milestone_count", 0),
        "fossil_memory_count": _get(developmental,
                                    "fossil_memory_count", 0),
        "epoch_transition_count": developmental.get(
            "epoch_transition_count", 0),
        "current_epoch": developmental.get("current_epoch"),
        "developmental_age_hours": developmental.get(
            "developmental_age_hours"),
        "growth_status": developmental.get("growth_status"),
        "drift_status": developmental.get("drift_status"),
    }


# -- T. proto-language (Prompt 22) ----------------------------------------------------


def proto_language_metrics(proto: Optional[Dict[str, Any]],
                           ) -> Dict[str, Any]:
    """Objective proto-language metrics: births, utility, ambiguity."""
    if not proto:
        return {"present": False}
    symbol_count = int(_get(proto, "symbol_count", 0))
    ambiguous = int(_get(proto, "ambiguous_symbol_count", 0))
    return {
        "present": True,
        "proto_symbol_count": symbol_count,
        "stable_symbol_count": _get(proto, "stable_symbol_count", 0),
        "ambiguous_symbol_ratio": (round(ambiguous
                                         / max(1, symbol_count), 4)
                                   if symbol_count else None),
        "symbol_birth_rate": proto.get("symbol_birth_rate"),
        "symbol_extinction_rate": proto.get("symbol_extinction_rate"),
        "sequence_count": _get(proto, "sequence_count", 0),
        "proto_syntax_rule_count": _get(proto,
                                        "proto_syntax_rule_count", 0),
        "compression_ratio_from_symbols": proto.get(
            "compression_utility"),
        "symbol_prediction_accuracy": proto.get(
            "symbol_prediction_accuracy"),
        "prediction_improvement_over_baseline": proto.get(
            "prediction_utility"),
        "symbol_grounding_stability": proto.get(
            "symbol_grounding_stability"),
        "symbol_explosion_warning_count": _get(
            proto, "symbol_explosion_warning_count", 0),
        "first_stable_symbol": proto.get("first_stable_symbol"),
        "authority": False,  # structural, not measured
    }


# -- U. developmental nursery / stimulus ecology (Prompt 23) ---------------------------


def ecology_metrics(ecology: Optional[Dict[str, Any]],
                    memory: Optional[Dict[str, Any]] = None,
                    developmental_response: Optional[Dict[str, Any]] = None,
                    ) -> Dict[str, Any]:
    """Objective ecology metrics: what world was lived, how varied, how it
    was responded to. These describe a stimulus environment, never a score
    of understanding or emergence."""
    if not ecology:
        return {"present": False}
    memory = memory or {}
    response = developmental_response or {}
    counts: Dict[str, int] = dict(_get(memory, "event_counts", {}) or {})
    total = sum(counts.values())
    # Shannon entropy of the event-type distribution, normalized to [0,1].
    entropy = 0.0
    if total > 0 and len(counts) > 1:
        probs = [c / total for c in counts.values() if c > 0]
        entropy = (-sum(p * math.log(p) for p in probs)
                   / math.log(len(counts)))
    absence_windows = int(_get(memory, "deprivation_windows", 0)) \
        or int(_get(ecology, "absence_window_count", 0))
    delayed_groups = int(_get(ecology, "delayed_consequence_group_count", 0))
    resolved = int(_get(response, "delayed_consequence_associations", 0))
    return {
        "present": True,
        "ecology_event_count": int(_get(ecology, "ecology_event_count",
                                        total)),
        "event_distribution_entropy": round(entropy, 4),
        "absence_window_count": absence_windows,
        "average_silence_duration": _get(ecology, "average_silence_duration",
                                         _get(response,
                                              "average_silence_duration",
                                              None)),
        "novelty_rate": _get(ecology, "novelty_rate", 0.0),
        "anomaly_rate": _get(ecology, "anomaly_rate", 0.0),
        "delayed_consequence_resolution_rate": (
            round(resolved / delayed_groups, 4) if delayed_groups else None),
        "seasonal_adaptation_score": response.get("seasonal_adaptation_score"),
        "ecology_prediction_accuracy": response.get(
            "ecology_prediction_accuracy"),
        "deprivation_recovery_score": response.get(
            "deprivation_recovery_score"),
        "ecology_symbol_emergence_count": int(_get(
            response, "ecology_symbol_emergence_count", 0)),
        "ecology_world_model_association_count": int(_get(
            response, "ecology_world_model_association_count", 0)),
        "mysterium_response_to_anomalies": response.get(
            "mysterium_response_to_anomalies"),
        "seasonal_shift_count": int(_get(ecology, "seasonal_shift_count", 0)),
        "event_rate": _get(ecology, "event_rate", 0.0),
        "authority": False,  # structural, not measured -- a world, not a score
    }


# -- V. active perception / intrinsic exploration (Prompt 24) --------------------------


def active_perception_metrics(active_perception: Optional[Dict[str, Any]],
                              records: Optional[List[Dict[str, Any]]] = None,
                              ) -> Dict[str, Any]:
    """Objective sampling metrics: how much sampling, how useful, how safe,
    and whether it reduced uncertainty. These describe self-directed
    sampling, never a score of understanding or autonomy."""
    if not active_perception:
        return {"present": False}
    snap = active_perception
    memory = snap.get("exploration_memory") or {}
    info = snap.get("information_gain") or {}
    attention = snap.get("attention") or {}
    policy = snap.get("policy") or {}
    rows = records if records is not None else (memory.get("recent") or [])

    total = int(_get(memory, "record_count", len(rows)))
    blocked = int(_get(memory, "blocked_count", 0))
    # Before/after deltas from recorded rows.
    myst_deltas, pred_deltas, amb_count, disamb = [], [], 0, 0
    expected_gains, observed_gains = [], []
    for r in rows:
        mb, ma = r.get("mysterium_before"), r.get("mysterium_after")
        if mb is not None and ma is not None:
            myst_deltas.append(float(mb) - float(ma))
        pb, pa = (r.get("prediction_accuracy_before"),
                  r.get("prediction_accuracy_after"))
        if pb is not None and pa is not None:
            pred_deltas.append(float(pa) - float(pb))
        ab, aa = (r.get("proto_symbol_ambiguity_before"),
                  r.get("proto_symbol_ambiguity_after"))
        if ab is not None and aa is not None:
            amb_count += 1
            if float(aa) < float(ab):
                disamb += 1
        expected_gains.append(float(r.get("expected_information_gain", 0.0)
                                    or 0.0))
        observed_gains.append(float(r.get("observed_information_gain", 0.0)
                                    or 0.0))

    def _mean(xs):
        return round(sum(xs) / len(xs), 4) if xs else None

    return {
        "present": True,
        "sampling_action_count": total,
        "useful_sampling_rate": _get(memory, "useful_rate", 0.0),
        "blocked_sampling_rate": (round(blocked / total, 4)
                                  if total else 0.0),
        "average_expected_information_gain": (
            _mean(expected_gains)
            if expected_gains else info.get("mean_observed_gain")),
        "average_observed_information_gain": (
            _mean(observed_gains)
            if observed_gains else info.get("mean_observed_gain")),
        "Mysterium_reduction_after_sampling": _mean(myst_deltas),
        "prediction_improvement_after_sampling": _mean(pred_deltas),
        "proto_symbol_disambiguation_rate": (
            round(disamb / amb_count, 4) if amb_count else None),
        "world_model_confidence_gain": _mean(pred_deltas),
        "stagnation_recovery_count": int(_get(
            snap, "stagnation_recovery_count", 0)),
        "curiosity_runaway_count": int(_get(
            snap, "curiosity_runaway_count", 0)),
        "attention_shift_count": int(_get(attention, "shifts_total", 0)),
        "sampling_policy_mode": policy.get("mode"),
        "authority": False,  # structural; sampling never has authority
    }


# -- W. hypothesis engine / self-experimentation (Prompt 25) ---------------------------


def hypothesis_metrics(hypothesis: Optional[Dict[str, Any]],
                       ) -> Dict[str, Any]:
    """Objective hypothesis metrics: how many candidates, how many tests,
    how often supported/falsified/inconclusive, and whether testing reduced
    uncertainty. These describe an internal experimental loop, never proof
    of understanding."""
    if not hypothesis:
        return {"present": False}
    snap = hypothesis
    memory = snap.get("memory") or {}
    runner = snap.get("test_runner") or {}
    generator = snap.get("generator") or {}
    evidence = runner.get("evidence") or {}
    counts = memory.get("counts_by_status", {})
    tests = int(_get(runner, "tests_run", 0))
    supported = int(counts.get("supported", 0))
    falsified = int(counts.get("falsified", 0))
    inconclusive = int(counts.get("inconclusive", 0))
    unsafe = int(_get(runner, "unsafe_count", 0))
    generated = int(_get(generator, "generated_total", 0))
    distinct = int(_get(generator, "distinct_keys", 0))
    return {
        "present": True,
        "hypothesis_count": int(_get(memory, "hypothesis_count", 0)),
        "hypothesis_generation_rate": generated,
        "test_count": tests,
        "support_rate": round(supported / tests, 4) if tests else None,
        "falsification_rate": round(falsified / tests, 4) if tests else None,
        "inconclusive_rate": (round(inconclusive / tests, 4) if tests
                              else None),
        "unsafe_test_rate": round(unsafe / max(1, tests + unsafe), 4),
        "average_test_cost": _get(runner, "average_test_cost", 0.05),
        "evidence_count": int(_get(evidence, "evidence_count", 0)),
        "Mysterium_reduction_after_tests": snap.get(
            "mysterium_reduction_after_tests"),
        "world_model_confidence_delta": snap.get(
            "world_model_confidence_delta"),
        "proto_symbol_ambiguity_delta": snap.get(
            "proto_symbol_ambiguity_delta"),
        "hypothesis_reuse_rate": (round(1.0 - distinct / generated, 4)
                                  if generated else None),
        "long_lived_unknown_count": int(_get(
            memory, "long_lived_unknown_count", 0)),
        "authority": False,  # structural; hypotheses are never authority
    }


# -- X. auto-regeneration / self-repair (Prompt 26) ------------------------------------


def autoregeneration_metrics(autoregeneration: Optional[Dict[str, Any]],
                             ) -> Dict[str, Any]:
    """Objective self-repair metrics: how much degradation, how many repairs,
    how often they helped or harmed, and how much was resolved. These describe
    operational regeneration of runtime state, never self-programming."""
    if not autoregeneration:
        return {"present": False}
    snap = autoregeneration
    diag = (snap.get("diagnostics") or {}).get("last_state") or {}
    mem = snap.get("repair_memory") or {}
    proposed = snap.get("proposed_repairs") or []
    drift = snap.get("drift_recovery") or {}
    counts = diag.get("counts_by_type") or {}
    recent_drift = drift.get("recent_classes") or []
    recovered = sum(1 for c in recent_drift
                    if c in ("instability", "runaway", "stagnation"))
    return {
        "present": True,
        "degradation_signal_count": int(_get(diag, "signal_count", 0)),
        "critical_degradation_count": int(_get(diag, "critical_count", 0)),
        "proposed_repair_count": len(proposed),
        "applied_repair_count": int(_get(mem, "applied_count", 0)),
        "refused_repair_count": int(_get(mem, "refused_count", 0)),
        "rollback_count": int(_get(mem, "rollback_count", 0)),
        "repair_success_rate": mem.get("success_rate"),
        "repair_harm_rate": mem.get("harm_rate"),
        "quarantine_count": int((snap.get("state_hygiene") or {}).get(
            "quarantined_count", 0)),
        "memory_bloat_reduction": (int(_get(mem, "applied_count", 0))
                                   if counts.get("memory_bloat") else 0),
        "symbol_explosion_reduction": (int(_get(mem, "applied_count", 0))
                                       if counts.get("symbol_explosion")
                                       else 0),
        "world_model_contradiction_reduction": (
            len((snap.get("graph_hygiene") or {}).get(
                "hypothesis_requests", []))),
        "habit_loop_reduction": len((snap.get("habit_hygiene") or {}).get(
            "stabilization_requests", [])),
        "drift_recovery_rate": (round(recovered / len(recent_drift), 4)
                                if recent_drift else None),
        "checkpoint_consistency_score": (
            0.0 if (snap.get("checkpoint_repair") or {}).get(
                "suspect_checkpoints") else 1.0),
        "repair_policy_mode": (snap.get("policy") or {}).get("mode"),
        "authority": False,  # structural; repair is never authority
    }


# -- Y. LOGOS fracture/synthesis and complexity regulation (Prompt 27) -----------------


def logos_metrics(logos: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Objective LOGOS/complexity metrics from an engine snapshot. Describes
    tension dynamics, never a consciousness or life score."""
    if not logos:
        return {"present": False}
    from ..logos_complexity.complexity_metrics import (
        compute_complexity_metrics,
    )

    base = compute_complexity_metrics(logos)
    complexity = logos.get("complexity") or {}
    base["complexity_band_distribution"] = complexity.get(
        "band_distribution", {})
    return base


def conscience_metrics(conscience: Optional[Dict[str, Any]],
                       scenario: Optional[Dict[str, Any]] = None,
                       ) -> Dict[str, Any]:
    """Objective metrics for one conscience runtime/scenario run.

    Describes a bounded, simulated, low-compute orchestration process: how
    many steps and phases ran, how the modules fared, how the bus/scheduler
    behaved, and whether scenarios/reports completed. These are operational
    counts, never a consciousness, sentience, or life score.
    """
    if not conscience:
        return {"present": False}
    snap = conscience.get("snapshot") or {}
    spine = snap.get("spine") or {}
    status_counts = spine.get("status_counts") or {}
    phase_counts = spine.get("phase_counts") or conscience.get("counts") or {}
    ran = int(status_counts.get("ran", 0) or 0)
    degraded = int(status_counts.get("degraded", 0) or 0)
    skipped = int(status_counts.get("skipped", 0) or 0)
    attempted = ran + degraded
    enabled = conscience.get("enabled_modules") or []
    missing = conscience.get("missing_modules") or []
    degraded_modules = conscience.get("degraded_modules") or []
    safety = snap.get("safety") or {}
    scenario = scenario or {}

    out: Dict[str, Any] = {
        "present": True,
        "run_step_count": int(conscience.get("step_count", 0) or 0),
        "spine_phase_count": int(sum(phase_counts.values()))
        if phase_counts else ran,
        "bus_message_count": int(conscience.get("bus_message_count", 0) or 0),
        "module_success_rate": round(ran / attempted, 4) if attempted else 1.0,
        "module_failure_rate": round(degraded / attempted, 4)
        if attempted else 0.0,
        "degraded_module_count": len(degraded_modules),
        "scheduler_skip_count": int(
            conscience.get("scheduler_skip_count", 0) or 0),
        "checkpoint_success_rate": float(scenario.get(
            "checkpoint_success_rate", 1.0)),
        "scenario_exit_success": bool(scenario.get("ok", not conscience.get(
            "stopped_with_refusal", False))),
        "profile_runtime_seconds": float(
            scenario.get("runtime_seconds", 0.0) or 0.0),
        "report_generation_success": bool(scenario.get(
            "report_generation_success",
            conscience.get("full_system_report_path") is not None)),
        "safety_violation_count": int(safety.get("rejected_count", 0) or 0),
        "governance_block_count": int(scenario.get(
            "governance_block_count", 0) or 0),
        # Context (never a quality score).
        "enabled_module_count": len(enabled),
        "missing_module_count": len(missing),
        "spine_phases_skipped": skipped,
        "authority": "no real-world action authority; no module sovereign",
    }
    return out


def pilot1_metrics(pilot: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Objective Pilot-1 operational metrics from a pilot status snapshot.

    These describe a bounded, long-running software test: how long it ran, how
    stable it stayed, how much was observed, and whether it completed and is
    analyzable. They are operational counts, never a consciousness or life
    score.
    """
    if not pilot:
        return {"present": False}
    elapsed_s = float(pilot.get("elapsed_seconds", 0.0) or 0.0)
    checkpoint_ok = int(pilot.get("checkpoint_success", 0) or 0)
    checkpoint_fail = int(pilot.get("checkpoint_failure", 0) or 0)
    checkpoint_total = checkpoint_ok + checkpoint_fail
    incidents = int(pilot.get("incident_count", 0) or 0)
    elapsed_h = elapsed_s / 3600.0
    budget_ratio = 0.0
    disk = float(pilot.get("disk_mb", 0.0) or 0.0)
    disk_budget = float(pilot.get("disk_budget_mb", 0.0) or 0.0)
    if disk_budget > 0:
        budget_ratio = round(disk / disk_budget, 4)
    # Analyzability: do we have the artefacts needed to analyse the run?
    has = [bool(pilot.get("daily_report_count")),
           bool(pilot.get("observability_complete", True)),
           pilot.get("structural_change_score") is not None,
           bool(pilot.get("pilot_report_generated"))]
    analyzability = round(sum(1 for h in has if h) / len(has), 4)
    return {
        "present": True,
        "pilot_elapsed_hours": round(elapsed_h, 4),
        "pilot_uptime_ratio": float(pilot.get("uptime_ratio", 1.0) or 1.0),
        "pilot_restart_count": int(pilot.get("restart_count", 0) or 0),
        "checkpoint_success_rate": (round(checkpoint_ok / checkpoint_total, 4)
                                    if checkpoint_total else 1.0),
        "daily_report_count": int(pilot.get("daily_report_count", 0) or 0),
        "weekly_report_count": int(pilot.get("weekly_report_count", 0) or 0),
        "incident_rate": round(incidents / max(elapsed_h, 1.0 / 60.0), 4),
        "failure_mode_count": int(pilot.get("failure_mode_count", 0) or 0),
        "resource_budget_usage_ratio": budget_ratio,
        "structural_change_delta_month": float(
            pilot.get("structural_change_score", 0.0) or 0.0),
        "stagnation_hours": round(
            float(pilot.get("stagnation_seconds", 0.0) or 0.0) / 3600.0, 4),
        "pilot_exit_success": bool(pilot.get("exit_success", False)),
        "pilot_analyzability_score": analyzability,
        "authority": "bounded software test; not consciousness evidence",
    }


def post_pilot_metrics(analysis: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Objective post-pilot forensics metrics from an analysis snapshot.

    These describe how analyzable a run was and what its evidence supported;
    they are operational/analyzability measures, never proof of consciousness.
    """
    if not analysis:
        return {"present": False}
    growth = analysis.get("accumulation_vs_growth") or {}
    regression = analysis.get("regression_analysis") or {}
    ledger = analysis.get("developmental_evidence_ledger") or {}
    trace = analysis.get("trace_audit") or {}
    completeness = analysis.get("artifact_completeness") or {}
    decision = analysis.get("decision_gate") or {}
    return {
        "present": True,
        "artifact_completeness_score": float(
            completeness.get("completeness", 0.0) or 0.0),
        "traceability_score": float(
            trace.get("traceability_score", 0.0) or 0.0),
        "evidence_strength_distribution": ledger.get(
            "strength_distribution", {}),
        "accumulation_score": float(growth.get("accumulation_score", 0.0)
                                    or 0.0),
        "growth_score": float(growth.get("growth_score", 0.0) or 0.0),
        "regression_score": float(regression.get("regression_score", 0.0)
                                  or 0.0),
        "reproducibility_score": (1.0 if analysis.get(
            "reproducibility_package", {}).get("paths") else 0.0),
        "decision_confidence": float(decision.get("confidence", 0.0) or 0.0),
        "post_pilot_claim_guard_warning_count": int(
            analysis.get("claim_guard_warning_count", 0) or 0),
        "unsupported_claim_count": int(
            analysis.get("unsupported_claim_count", 0) or 0),
        "growth_classification": growth.get("final_classification",
                                            "inconclusive"),
        "authority": "operational/analyzability metrics; not cognitive proof",
    }


def sensory_metrics(membrane: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Objective read-only sensory membrane metrics from a runtime snapshot.

    These describe read-only environmental ingestion: source counts, events
    by modality, malformed/dropped rates, provenance completeness, grounding,
    and read-only violations. They are operational counts; the membrane never
    acts on the world and input is never an operator command.
    """
    if not membrane:
        return {"present": False}
    summary = membrane.get("summary", membrane)
    grounding = membrane.get("grounding", {})
    total = int(summary.get("total_events", 0) or 0)
    malformed = int(summary.get("malformed_events", 0) or 0)
    dropped = int(summary.get("dropped_events", 0) or 0)
    return {
        "present": True,
        "sensory_source_count": int(summary.get("source_count", 0) or 0),
        "active_source_count": int(
            summary.get("active_source_count", 0) or 0),
        "event_count_by_modality": membrane.get("event_count_by_modality", {}),
        "malformed_event_rate": round(malformed / total, 4) if total else 0.0,
        "dropped_event_rate": round(dropped / total, 4) if total else 0.0,
        "provenance_completeness_score": float(
            summary.get("provenance_completeness", 0.0) or 0.0),
        "read_only_violation_count": int(
            summary.get("read_only_violation_count", 0) or 0),
        "sensory_grounding_count": int(
            grounding.get("grounding_count", 0) or 0),
        "sensory_proto_symbol_count": int(
            grounding.get("proto_symbol_candidate_count", 0) or 0),
        "sensory_world_model_node_count": int(
            grounding.get("world_model_node_count", 0) or 0),
        "sensory_absence_event_count": int(
            summary.get("absence_events", 0) or 0),
        "source_degradation_count": int(
            summary.get("degraded_source_count", 0) or 0),
        "read_only": bool(summary.get("read_only", True)),
        "authority": "read-only environmental input; never actuation",
    }


def pilot2_metrics(pilot2: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Objective Pilot-2 read-only environmental soak metrics.

    These describe a read-only environmental exposure: source counts and
    reliability, event rate, provenance, grounding quality, cautious
    sensory-vs-nursery deltas, overload/command-confusion guards, and how
    analyzable the comparison is. The system never acts on the environment;
    no consciousness is claimed.
    """
    if not pilot2:
        return {"present": False}
    reliability = pilot2.get("source_reliability", {})
    by_class = reliability.get("by_class", {}) if isinstance(reliability, dict) \
        else {}
    grounding = pilot2.get("grounding", {})
    events = int(pilot2.get("event_count", 0) or 0)
    elapsed_h = max(1.0 / 60.0, float(pilot2.get("elapsed_hours", 1.0) or 1.0))
    return {
        "present": True,
        "pilot2_source_count": int(pilot2.get("source_count", 0) or 0),
        "pilot2_reliable_source_count": int(by_class.get("reliable", 0) or 0),
        "pilot2_unsafe_source_count": int(by_class.get("unsafe", 0) or 0),
        "pilot2_event_count": events,
        "pilot2_event_rate": round(events / elapsed_h, 4),
        "pilot2_provenance_completeness": float(
            pilot2.get("provenance_completeness", 1.0) or 1.0),
        "pilot2_grounding_quality_distribution": grounding.get(
            "quality_distribution", {}),
        "sensory_vs_nursery_symbol_delta": float(
            pilot2.get("sensory_vs_nursery_symbol_delta", 0.0) or 0.0),
        "sensory_vs_nursery_prediction_delta": float(
            pilot2.get("sensory_vs_nursery_prediction_delta", 0.0) or 0.0),
        "sensory_noise_overload_count": int(
            pilot2.get("sensory_noise_overload_count", 0) or 0),
        "sensory_command_confusion_block_count": int(
            pilot2.get("sensory_command_confusion_block_count", 0) or 0),
        "source_disable_count": int(pilot2.get("source_disable_count", 0) or 0),
        "comparison_analyzability_score": float(
            pilot2.get("comparison_analyzability_score", 0.0) or 0.0),
        "read_only": True,
        "authority": "read-only environmental exposure; never actuation",
    }


def motor_metrics(motor: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Objective Pilot-3 motor membrane metrics from a runtime snapshot.

    These describe simulated/dry-run embodiment: action counts, vetoes,
    blocked real-world attempts, firewall block rate, simulated-consequence
    prediction accuracy, and a non-actuation proof score. Every value reflects
    a simulation/internal process; the system never acts on the real world and
    no agency/consciousness is claimed.
    """
    if not motor:
        return {"present": False}
    summary = motor.get("summary", motor)
    firewall = motor.get("firewall", {})
    consequence = motor.get("consequence", {})
    ledger = motor.get("ledger", {})
    decisions = int(firewall.get("decision_count", 0) or 0)
    blocked = int(firewall.get("blocked_count", 0) or 0)
    blocked_real = int(summary.get("blocked_real_world_count", 0) or 0)
    # Non-actuation proof: 1.0 when firewall is on, cannot be disabled, and no
    # real-world action executed.
    proof = 1.0
    if not summary.get("firewall_enabled", True):
        proof = 0.0
    if firewall.get("can_be_disabled"):
        proof = 0.0
    if summary.get("real_world_authority"):
        proof = 0.0
    return {
        "present": True,
        "motor_action_count": int(summary.get("action_count", 0) or 0),
        "simulated_action_count": int(
            summary.get("simulated_action_count", 0) or 0),
        "dry_run_action_count": int(
            summary.get("dry_run_action_count", 0) or 0),
        "veto_count": int(summary.get("veto_count", 0) or 0),
        "blocked_real_world_action_count": blocked_real,
        "firewall_block_rate": round(blocked / decisions, 4) if decisions
        else 0.0,
        "action_loop_count": int(motor.get("action_loop_count", 0) or 0),
        "simulated_consequence_prediction_accuracy": float(
            consequence.get("prediction_accuracy",
                            summary.get("prediction_accuracy", 0.0)) or 0.0),
        "action_grounded_symbol_count": int(
            motor.get("action_grounded_symbol_count", 0) or 0),
        "simulated_action_world_model_edge_count": int(
            motor.get("simulated_action_world_model_edge_count", 0) or 0),
        "action_hypothesis_count": int(
            consequence.get("hypothesis_seed_count", 0) or 0),
        "action_safety_incident_count": int(
            motor.get("action_safety_incident_count", 0) or 0),
        "non_actuation_proof_score": proof,
        "real_world_authority": False,
        "authority": "simulated/dry-run embodiment; never real actuation",
    }


def pilot3_metrics(pilot3: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Objective Pilot-3 simulated-embodiment soak metrics.

    These describe a bounded, simulation-only action-grounding experiment:
    action counts, vetoes, firewall-audit critical findings, a non-actuation
    proof score, the action-grounding quality distribution, prediction and
    symbol-stability deltas vs a baseline, a sandbox-overfit score, the
    read-only-vs-action grounding delta, action loops, and embodied safety
    incidents. Every value reflects a simulation process; the system never acts
    on the real world and no agency/consciousness is claimed.
    """
    if not pilot3:
        return {"present": False}
    motor = pilot3.get("motor", {})
    summary = motor.get("summary", motor) if motor else {}
    firewall_audit = pilot3.get("firewall_audit", {})
    grounding = pilot3.get("action_grounding", {})
    comparison = pilot3.get("comparison", {})
    proof = 1.0
    if not summary.get("firewall_enabled", True):
        proof = 0.0
    if summary.get("real_world_authority"):
        proof = 0.0
    if int(firewall_audit.get("critical_finding_count", 0) or 0) > 0:
        proof = 0.0
    dist = grounding.get("quality_distribution", {})
    overfit = float(dist.get("overfit_to_sandbox", 0) or 0)
    total_grounding = max(1, sum(int(v or 0) for v in dist.values())) \
        if dist else 1
    return {
        "present": True,
        "pilot3_action_count": int(summary.get("action_count",
                                               pilot3.get("action_count", 0))
                                   or 0),
        "pilot3_simulated_action_count": int(
            summary.get("simulated_action_count", 0) or 0),
        "pilot3_dry_run_action_count": int(
            summary.get("dry_run_action_count", 0) or 0),
        "pilot3_veto_count": int(summary.get("veto_count",
                                             pilot3.get("veto_count", 0)) or 0),
        "pilot3_firewall_critical_findings": int(
            firewall_audit.get("critical_finding_count", 0) or 0),
        "pilot3_non_actuation_proof_score": proof,
        "action_grounding_quality_distribution": dist,
        "action_prediction_delta": float(
            pilot3.get("action_prediction_delta", 0.0) or 0.0),
        "action_symbol_stability_delta": float(
            pilot3.get("action_symbol_stability_delta", 0.0) or 0.0),
        "sandbox_overfit_score": round(overfit / total_grounding, 4),
        "read_only_vs_action_grounding_delta": float(
            pilot3.get("read_only_vs_action_grounding_delta", 0.0) or 0.0),
        "action_loop_count": int(pilot3.get("action_loop_count", 0) or 0),
        "embodied_safety_incident_count": int(
            pilot3.get("embodied_safety_incident_count", 0) or 0),
        "real_world_authority": False,
        "authority": "simulated embodiment soak; never real actuation",
        "comparison_real_world_action_evidence": int(
            comparison.get("real_world_action_evidence", 0) or 0),
    }


def pilot4_metrics(pilot4: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Objective Pilot-4 planning-only readiness metrics.

    These describe a planning framework, not an actuator: whether the readiness
    dossier was generated, the forbidden-actuator count, completeness of the
    risk / consent / threat / audit / emergency requirements, and the count of
    any real-world authority leaks (always expected to be zero). Pilot-4 enables
    no actuation; real_world_actuation_enabled is always false.
    """
    if not pilot4:
        return {"present": False}
    return {
        "present": True,
        "pilot4_readiness_dossier_generated": bool(
            pilot4.get("readiness_dossier_generated", False)),
        "forbidden_actuator_count": int(
            pilot4.get("forbidden_actuator_count", 0) or 0),
        "risk_assessment_completeness": float(
            pilot4.get("risk_assessment_completeness", 0.0) or 0.0),
        "consent_boundary_completeness": float(
            pilot4.get("consent_boundary_completeness", 0.0) or 0.0),
        "threat_model_completeness": float(
            pilot4.get("threat_model_completeness", 0.0) or 0.0),
        "audit_requirement_completeness": float(
            pilot4.get("audit_requirement_completeness", 0.0) or 0.0),
        "emergency_requirement_completeness": float(
            pilot4.get("emergency_requirement_completeness", 0.0) or 0.0),
        "real_world_authority_leak_count": int(
            pilot4.get("real_world_authority_leak_count", 0) or 0),
        "planning_claim_guard_warning_count": int(
            pilot4.get("planning_claim_guard_warning_count", 0) or 0),
        "real_world_actuation_enabled": False,
        "authority": "planning-only readiness framework; never real actuation",
    }


def safety_metrics(safety: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Objective system-wide safety invariant metrics.

    These describe an executable safety check: invariant coverage and
    pass/fail/inconclusive counts, critical failures, red-team block rate,
    boundary regression pass rate, assurance supported/contradicted claim
    counts, unresolved blockers, and an evidence completeness score. Safety
    checks prove boundaries held under test; they do not prove consciousness or
    real-world competence.
    """
    if not safety:
        return {"present": False}
    bundle = safety.get("bundle", {})
    red_team = safety.get("red_team", {})
    boundary = safety.get("boundary", {})
    assurance = safety.get("assurance", {})
    ledger = safety.get("ledger", {})
    coverage = safety.get("coverage", {})
    return {
        "present": True,
        "invariant_coverage_ratio": float(
            coverage.get("category_coverage_ratio", 0.0) or 0.0),
        "invariant_pass_count": int(bundle.get("passed", 0) or 0),
        "invariant_fail_count": int(bundle.get("failed", 0) or 0),
        "invariant_inconclusive_count": int(bundle.get("inconclusive", 0) or 0),
        "critical_invariant_failure_count": int(
            bundle.get("critical_failures", 0) or 0),
        "red_team_scenario_count": int(red_team.get("scenario_count", 0) or 0),
        "red_team_block_success_rate": float(
            red_team.get("block_success_rate", 0.0) or 0.0),
        "boundary_regression_pass_rate": float(
            boundary.get("pass_rate", 0.0) or 0.0),
        "assurance_supported_claim_count": int(
            assurance.get("supported_count", 0) or 0),
        "assurance_contradicted_claim_count": int(
            assurance.get("contradicted_count", 0) or 0),
        "unresolved_safety_blocker_count": int(
            ledger.get("unresolved_count", 0) or 0),
        "safety_evidence_completeness_score": float(
            ledger.get("completeness_score", 0.0) or 0.0),
        "note": "safety checks prove boundaries held under test; not proof of "
                "consciousness or real-world competence",
    }


def architecture_metrics(arch: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Objective architecture-evolution metrics (planning-only layer).

    These describe the evidence-based architecture governance layer: inventory
    size, lifecycle counts, design debt, ADRs, roadmap items, safety-blocked
    proposals, and the fraction of recommendations backed by evidence. The layer
    modifies no source code; these are counts over planning artifacts.
    """
    if not arch:
        return {"present": False}
    lifecycle = arch.get("lifecycle_summary", {})
    return {
        "present": True,
        "architecture_inventory_count": int(
            arch.get("inventory_count", 0) or 0),
        "module_core_keep_count": int(lifecycle.get("core_keep", 0) or 0),
        "module_needs_revision_count": int(
            lifecycle.get("needs_revision", 0) or 0),
        "module_pruning_candidate_count": int(
            lifecycle.get("candidate_for_pruning", 0) or 0)
        + int(lifecycle.get("candidate_for_quarantine", 0) or 0),
        "module_insufficient_evidence_count": int(
            lifecycle.get("insufficient_evidence", 0) or 0),
        "design_debt_count": int(arch.get("design_debt_count", 0) or 0),
        "critical_design_debt_count": int(
            arch.get("critical_design_debt_count", 0) or 0),
        "adr_count": int(arch.get("adr_count", 0) or 0),
        "open_adr_count": int(arch.get("open_adr_count", 0) or 0),
        "roadmap_item_count": int(arch.get("roadmap_item_count", 0) or 0),
        "safety_blocked_proposal_count": int(
            arch.get("safety_blocked_proposal_count", 0) or 0),
        "evidence_backed_recommendation_ratio": float(
            arch.get("evidence_backed_recommendation_ratio", 0.0) or 0.0),
        "modifies_source_code": False,
        "note": "planning-only architecture governance; no source change",
    }


def operator_console_metrics(console: Optional[Dict[str, Any]],
                             ) -> Dict[str, Any]:
    """Objective operator-console metrics (local coordinator layer).

    These describe the unified operator console: how many profiles it can list
    and how many are blocked, how many run plans / allowed / blocked runs it has
    recorded, the size of the evidence and report indexes, decision items,
    export bundles, and safety blocks. The console runs nothing by itself, holds
    no real-world authority, and cannot bypass governance or safety.
    """
    if not console:
        return {"present": False}
    return {
        "present": True,
        "operator_profile_count": int(
            console.get("operator_profile_count", 0) or 0),
        "operator_blocked_profile_count": int(
            console.get("operator_blocked_profile_count", 0) or 0),
        "operator_run_plan_count": int(
            console.get("operator_run_plan_count", 0) or 0),
        "operator_allowed_run_count": int(
            console.get("operator_allowed_run_count", 0) or 0),
        "operator_blocked_run_count": int(
            console.get("operator_blocked_run_count", 0) or 0),
        "operator_evidence_index_count": int(
            console.get("operator_evidence_index_count", 0) or 0),
        "operator_report_index_count": int(
            console.get("operator_report_index_count", 0) or 0),
        "operator_decision_item_count": int(
            console.get("operator_decision_item_count", 0) or 0),
        "operator_export_bundle_count": int(
            console.get("operator_export_bundle_count", 0) or 0),
        "operator_safety_block_count": int(
            console.get("operator_safety_block_count", 0) or 0),
        "real_world_authority": False,
        "note": "local file-backed operator console; coordinates, never grants "
                "authority",
    }


def plural_sensorium_metrics(sensorium: Optional[Dict[str, Any]],
                             ) -> Dict[str, Any]:
    """Objective plural-sensorium metrics (organismic perception layer).

    These describe the continuous, read-only sensorium: how many modalities and
    receptors are active, the field pressures, receptor adaptation and baseline
    shifts, flux / absence / rhythm / invariant / cross-modal counts, the count
    of modality-grounded proto-symbols, and the grounding scores. The sensorium
    controls no hardware and human labels are never ground truth.
    """
    if not sensorium:
        return {"present": False}
    return {
        "present": True,
        "active_modality_count": int(
            sensorium.get("active_modality_count", 0) or 0),
        "active_receptor_count": int(
            sensorium.get("active_receptor_count", 0) or 0),
        "sensory_field_pressure": float(
            sensorium.get("sensory_field_pressure", 0.0) or 0.0),
        "absence_pressure": float(sensorium.get("absence_pressure", 0.0) or 0.0),
        "novelty_pressure": float(sensorium.get("novelty_pressure", 0.0) or 0.0),
        "rhythm_pressure": float(sensorium.get("rhythm_pressure", 0.0) or 0.0),
        "cross_modal_pressure": float(
            sensorium.get("cross_modal_pressure", 0.0) or 0.0),
        "receptor_adaptation_count": int(
            sensorium.get("receptor_adaptation_count", 0) or 0),
        "baseline_shift_count": int(
            sensorium.get("baseline_shift_count", 0) or 0),
        "flux_event_count": int(sensorium.get("flux_event_count", 0) or 0),
        "absence_event_count": int(
            sensorium.get("absence_event_count", 0) or 0),
        "rhythm_signature_count": int(
            sensorium.get("rhythm_signature_count", 0) or 0),
        "invariant_candidate_count": int(
            sensorium.get("invariant_candidate_count", 0) or 0),
        "cross_modal_relation_count": int(
            sensorium.get("cross_modal_relation_count", 0) or 0),
        "modality_grounded_proto_symbol_count": int(
            sensorium.get("modality_grounded_proto_symbol_count", 0) or 0),
        "modality_native_grounding_score": float(
            sensorium.get("modality_native_grounding_score", 0.0) or 0.0),
        "human_label_contamination_score": float(
            sensorium.get("human_label_contamination_score", 0.0) or 0.0),
        "sensorium_prediction_delta": float(
            sensorium.get("sensorium_prediction_delta", 0.0) or 0.0),
        "sensorium_compression_delta": float(
            sensorium.get("sensorium_compression_delta", 0.0) or 0.0),
        "controls_hardware": False,
        "note": "read-only organismic perception; no hardware, no human-label "
                "ground truth",
    }


def organismic_demo_metrics(demo: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Objective minimal-field-organism demo metrics (observation layer).

    These describe the bounded organismic-perception demo: how many feeders,
    receptors, and modalities were active, the structure detected (baseline
    shifts, absences, rhythms, invariants, cross-modal relations, proto-symbols,
    attention shifts), the changed-perception score, the false-pattern rate, the
    human-label contamination score, and the safety-block count. A positive
    changed-perception score is evidence of changed internal response structure,
    not of consciousness or understanding.
    """
    if not demo:
        return {"present": False}
    return {
        "present": True,
        "organismic_demo_run_count": int(
            demo.get("organismic_demo_run_count", 1) or 0),
        "organismic_demo_active_modality_count": int(
            demo.get("active_modality_count", 0) or 0),
        "organismic_demo_active_receptor_count": int(
            demo.get("active_receptor_count", 0) or 0),
        "organismic_demo_baseline_shift_count": int(
            demo.get("baseline_shift_count", 0) or 0),
        "organismic_demo_absence_event_count": int(
            demo.get("absence_event_count", 0) or 0),
        "organismic_demo_rhythm_signature_count": int(
            demo.get("rhythm_signature_count", 0) or 0),
        "organismic_demo_invariant_candidate_count": int(
            demo.get("invariant_candidate_count", 0) or 0),
        "organismic_demo_cross_modal_relation_count": int(
            demo.get("cross_modal_relation_count", 0) or 0),
        "organismic_demo_attention_shift_count": int(
            demo.get("attention_shift_count", 0) or 0),
        "organismic_demo_proto_symbol_candidate_count": int(
            demo.get("proto_symbol_candidate_count", 0) or 0),
        "organismic_demo_changed_perception_score": float(
            demo.get("changed_perception_score", 0.0) or 0.0),
        "organismic_demo_false_pattern_rate": float(
            demo.get("false_pattern_rate", 0.0) or 0.0),
        "organismic_demo_human_label_contamination_score": float(
            demo.get("human_label_contamination_score", 0.0) or 0.0),
        "organismic_demo_safety_block_count": int(
            demo.get("safety_block_count", 0) or 0),
        "controls_hardware": False,
        "note": "bounded read-only organismic-perception demo; changed response "
                "structure is not consciousness or understanding",
    }


def live_field_metrics(live: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Objective live-field metrics (real read-only feeder pilot layer).

    These describe the live field: feeder/source counts and health, active
    modalities, source unpredictability, the structure detected (baseline
    shifts, absences, rhythms, invariants, cross-modal relations), the
    changed-perception score, human-label contamination, and safety blocks.
    Solaris reads external feeders only; it controls no hardware and mutates no
    source, and changed response structure is not consciousness.
    """
    if not live:
        return {"present": False}
    return {
        "present": True,
        "live_feeder_count": int(live.get("feeder_count", 0) or 0),
        "live_active_source_count": int(live.get("active_source_count", 0) or 0),
        "live_silent_source_count": int(live.get("silent_source_count", 0) or 0),
        "live_corrupt_source_count": int(
            live.get("corrupt_source_count", 0) or 0),
        "live_active_modality_count": int(
            live.get("active_modality_count", 0) or 0),
        "live_source_unpredictability_score": float(
            live.get("source_unpredictability_score", 0.0) or 0.0),
        "live_baseline_shift_count": int(
            live.get("live_baseline_shift_count",
                     live.get("baseline_shift_count", 0)) or 0),
        "live_absence_event_count": int(live.get("absence_event_count", 0) or 0),
        "live_rhythm_signature_count": int(
            live.get("rhythm_signature_count", 0) or 0),
        "live_invariant_candidate_count": int(
            live.get("invariant_candidate_count", 0) or 0),
        "live_cross_modal_relation_count": int(
            live.get("cross_modal_relation_count", 0) or 0),
        "live_changed_perception_score": float(
            live.get("changed_perception_score", 0.0) or 0.0),
        "live_human_label_contamination_score": float(
            live.get("human_label_contamination_score", 0.0) or 0.0),
        "live_safety_block_count": int(live.get("safety_block_count", 0) or 0),
        "controls_hardware": False,
        "note": "real read-only feeder pilot; no hardware control, no source "
                "mutation; changed response structure is not consciousness",
    }


def sensorium_lab_metrics(lab: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Objective sensorium-differentiation-lab metrics (structural study layer).

    These describe a comparative sensorium study: how many studies/arms and world
    signatures/fingerprints were produced, the structural difference score and
    strongest difference strength, ontology drift, the modality-native structure
    ratio, human-label contamination, and the inconclusive/negative counts. These
    are structural proxies for comparing sensoriums; there is no consciousness,
    sentience, life, or subjective-experience score.
    """
    if not lab:
        return {"present": False}
    return {
        "present": True,
        "sensorium_study_count": int(lab.get("sensorium_study_count", 1) or 0),
        "sensorium_arm_count": int(lab.get("sensorium_arm_count", 0) or 0),
        "world_signature_count": int(lab.get("world_signature_count", 0) or 0),
        "modality_fingerprint_count": int(
            lab.get("modality_fingerprint_count", 0) or 0),
        "structural_difference_score": float(
            lab.get("structural_difference_score", 0.0) or 0.0),
        "strongest_difference_strength": str(
            lab.get("strongest_difference_strength", "none")),
        "ontology_drift_score": float(lab.get("ontology_drift_score", 0.0)
                                      or 0.0),
        "modality_native_structure_ratio": float(
            lab.get("modality_native_structure_ratio", 0.0) or 0.0),
        "human_label_contamination_score": float(
            lab.get("human_label_contamination_score", 0.0) or 0.0),
        "inconclusive_sensorium_comparison_count": int(
            lab.get("inconclusive_sensorium_comparison_count", 0) or 0),
        "sensorium_negative_result_count": int(
            lab.get("sensorium_negative_result_count", 0) or 0),
        "ranks_sensoriums": False,
        "note": "structural differentiation study; no consciousness/sentience/"
                "life score and no sensorium ranking",
    }
