"""Complexity metrics -- objective measures of LOGOS dynamics.

These are operational counts and rates over tensions, synthesis, complexity
bands, and Esc triggers, plus a tension-to-growth delta. There is
deliberately **no consciousness score and no life score**.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


def _num(d: Optional[Dict[str, Any]], key: str, default: float = 0.0) -> float:
    try:
        return float((d or {}).get(key, default) or 0.0)
    except (TypeError, ValueError):
        return default


def compute_complexity_metrics(snapshot: Optional[Dict[str, Any]],
                               ) -> Dict[str, Any]:
    """Objective LOGOS/complexity metrics from an engine snapshot."""
    if not snapshot:
        return {"present": False}
    opposition = snapshot.get("opposition_memory") or {}
    synthesis = snapshot.get("synthesis") or {}
    complexity = snapshot.get("complexity") or {}
    esc = snapshot.get("esc") or {}
    fracture = snapshot.get("fracture") or {}
    trace = snapshot.get("dialectical_trace") or {}
    trace_counts = trace.get("counts") or {}

    proposed = _num(synthesis, "proposed_total")
    applied = _num(synthesis, "applied_total")
    refused = _num(synthesis, "refused_total")
    contradiction_detected = int((fracture.get("by_type") or {}).get(
        "world_model_contradiction", 0))
    hypotheses_spawned = int(trace_counts.get("hypothesis_spawned", 0))
    ambiguity_detected = int((fracture.get("by_type") or {}).get(
        "symbol_ambiguity", 0))
    splits = int(trace_counts.get("synthesis_applied", 0))

    return {
        "present": True,
        "tension_count": int(_num(opposition, "tension_count")),
        "unresolved_tension_count": int(_num(opposition,
                                             "unresolved_count")),
        "recurring_tension_count": int(_num(opposition, "recurring_count")),
        "synthesis_candidate_count": int(proposed),
        "synthesis_success_rate": (round(applied / (applied + refused), 4)
                                   if (applied + refused) else None),
        "synthesis_refusal_rate": (round(refused / (applied + refused), 4)
                                   if (applied + refused) else None),
        "preserved_tension_count": int(_num(opposition, "preserved_count")),
        "complexity_band": complexity.get("band"),
        "complexity_pressure_score": _num(
            (complexity.get("last_state") or {}).get("pressure") or {},
            "score"),
        "overload_warning_count": int(_num(complexity, "overload_warnings")),
        "inert_warning_count": int(_num(complexity, "inert_warnings")),
        "esc_trigger_count": int(_num(esc, "trigger_count")),
        "contradiction_to_hypothesis_rate": (
            round(hypotheses_spawned / contradiction_detected, 4)
            if contradiction_detected else None),
        "ambiguity_to_symbol_split_rate": (
            round(splits / ambiguity_detected, 4)
            if ambiguity_detected else None),
        "symbol_ambiguity_resolution_rate": (
            round(splits / ambiguity_detected, 4)
            if ambiguity_detected else None),
        "tension_to_growth_delta": snapshot.get("tension_to_growth_delta"),
        "tension_to_structural_change_delta": snapshot.get(
            "tension_to_growth_delta"),
        "authority": False,  # structural; LOGOS is never authority
    }
