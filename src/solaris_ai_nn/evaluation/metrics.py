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
