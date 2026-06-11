"""Long-horizon metrics -- cautious names for long-run numbers.

There is deliberately no consciousness score and no life score here. The
strongest claims this module can make are ``structural_change_score``,
``developmental_stability_score``, and
``long_horizon_adaptation_proxy`` -- numbers over recorded metrics with
names that say exactly how little they prove.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

# Names that must never exist in this codebase's metric vocabulary.
FORBIDDEN_METRIC_NAMES = ("consciousness_score", "life_score",
                          "sentience_score", "awareness_score")


def long_horizon_metrics(state: Optional[Dict[str, Any]],
                         ) -> Dict[str, Any]:
    """Compute the long-horizon metric set from a developmental state
    dict (clock + memory + monitors + milestones, duck-typed keys)."""
    if not state:
        return {"present": False}
    clock = state.get("clock", {})
    memory = state.get("memory", {})
    growth = state.get("growth", {})
    drift = state.get("drift", {})
    milestones = state.get("milestones", {})
    epochs = state.get("epochs", {})
    lifetime_s = float(clock.get("cumulative_lifetime_s", 0.0) or 0.0)
    lifetime_hours = round(lifetime_s / 3600.0, 4)
    milestone_count = int(milestones.get("count", 0) or 0)
    fossil_count = int(memory.get("fossil_count", 0) or 0)
    structural = float(growth.get("structural_change_score", 0.0) or 0.0)
    drift_velocity = float(drift.get("drift_velocity", 0.0) or 0.0)
    stagnation = int(growth.get("stagnation_windows", 0) or 0)
    identity_trend = float(state.get("identity_continuity", 1.0) or 1.0)
    boundary_violations = int(state.get("boundary_violation_count", 0)
                              or 0)
    return {
        "present": True,
        "lifetime_runtime_hours": lifetime_hours,
        "active_runtime_ratio": clock.get("active_runtime_ratio", 1.0),
        "restart_recovery_count": clock.get("restart_gap_count", 0),
        "consolidation_count": clock.get(
            "total_memory_consolidations", 0),
        "compression_ratio": memory.get("compression_ratio"),
        "fossil_memory_count": fossil_count,
        "stable_habit_half_life": state.get("stable_habit_half_life"),
        "world_model_growth_rate": (
            round(float(state.get("world_model_node_count", 0) or 0)
                  / max(1.0, lifetime_hours), 4)),
        "pruning_rate": (round(float(state.get("pruning_count", 0) or 0)
                               / max(1.0, lifetime_hours), 6)),
        "mysterium_volatility": state.get("mysterium_volatility"),
        "prediction_accuracy_month_trend": state.get(
            "prediction_accuracy_trend"),
        "drift_velocity": drift_velocity,
        "stagnation_duration": stagnation,
        "phase_transition_candidate_count": state.get(
            "phase_transition_candidates", 0),
        "identity_continuity_trend": identity_trend,
        "boundary_stability_score": round(
            max(0.0, 1.0 - 0.2 * boundary_violations), 4),
        "milestone_rate": (round(milestone_count
                                 / max(1.0, lifetime_hours), 6)),
        "fossil_memory_rate": (round(fossil_count
                                     / max(1.0, lifetime_hours), 6)),
        "epoch_transition_count": epochs.get("transition_count", 0),
        # The cautious headline numbers.
        "structural_change_score": structural,
        "developmental_stability_score": round(
            max(0.0, min(1.0, identity_trend
                         * (1.0 - min(1.0, drift_velocity))
                         * (1.0 - 0.1 * boundary_violations))), 4),
        "long_horizon_adaptation_proxy": round(
            min(1.0, structural + 0.05 * milestone_count), 4),
        "note": "no consciousness or life score exists; these are "
                "numbers over recorded metrics, named for how little "
                "they prove",
    }
