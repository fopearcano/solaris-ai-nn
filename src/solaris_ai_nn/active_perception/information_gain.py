"""Information gain -- a heuristic estimate of what sampling is worth.

Estimates are low-compute and explicitly heuristic: every estimate carries a
confidence and an uncertainty, and the estimator does not overclaim "gain"
when evidence is weak. After an action runs, ``score_observed_result``
compares before/after context to record an *observed* gain proxy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .sampling_actions import SamplingAction, SamplingActionType


def _num(d: Optional[Dict[str, Any]], key: str, default: float = 0.0) -> float:
    try:
        return float((d or {}).get(key, default) or 0.0)
    except (TypeError, ValueError):
        return default


# Per-action-type heuristic affinities: which pressures an action tends to
# relieve, and the base expected gain when that pressure is present.
_ACTION_AFFINITY = {
    SamplingActionType.REPLAY_UNCERTAIN_TRACE: ("mysterium_pressure", 0.5),
    SamplingActionType.INSPECT_WORLD_MODEL_NODE: ("world_model_uncertainty",
                                                  0.5),
    SamplingActionType.SAMPLE_UNKNOWN_REGION: ("world_model_uncertainty",
                                               0.55),
    SamplingActionType.INSPECT_PROTO_SYMBOL: ("proto_symbol_ambiguity", 0.5),
    SamplingActionType.SEEK_NOVELTY: ("developmental_stagnation", 0.45),
    SamplingActionType.SEEK_ABSENCE: ("overstimulation", 0.4),
    SamplingActionType.SAMPLE_KNOWN_PATTERN: ("prediction_error", 0.35),
    SamplingActionType.FOCUS_SIGNAL_SOURCE: ("prediction_error", 0.4),
    SamplingActionType.SAMPLE_BOUNDARY: ("world_model_uncertainty", 0.3),
    SamplingActionType.EMIT_SIMULATED_PING: ("world_model_uncertainty", 0.3),
    SamplingActionType.CONSOLIDATE_BEFORE_SAMPLING: ("memory_pressure", 0.4),
    SamplingActionType.LOOK: ("prediction_error", 0.3),
    SamplingActionType.REST: ("fatigue", 0.25),
    SamplingActionType.WAIT: ("overstimulation", 0.2),
    SamplingActionType.OBSERVE_SIDECAR_ONLY: ("world_model_uncertainty", 0.2),
    SamplingActionType.NO_SAMPLING_ACTION: ("", 0.0),
}


@dataclass
class InformationGainEstimate:
    """One heuristic value-of-information estimate (always hedged)."""

    action_id: str
    action_type: str
    expected_gain: float = 0.0  # [0, 1]
    confidence: float = 0.0     # [0, 1]
    uncertainty: float = 1.0    # [0, 1]; high when evidence is weak
    basis: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class InformationGainEstimator:
    """Heuristic VOI estimation; never overclaims under weak evidence."""

    history: List[Dict[str, Any]] = field(default_factory=list)

    def estimate_action(self, action: SamplingAction,
                        context: Dict[str, Any]) -> InformationGainEstimate:
        ctx = dict(context or {})
        pressure_key, base = _ACTION_AFFINITY.get(
            action.action_type, ("", 0.1))
        # The relevant pressure level scales the base gain.
        level = self._pressure_level(pressure_key, ctx)
        expected = round(base * level, 4)
        # Confidence rises with evidence; weak evidence => high uncertainty.
        evidence = self._evidence_strength(ctx)
        confidence = round(min(0.9, 0.2 + 0.7 * evidence * level), 4)
        uncertainty = round(1.0 - confidence, 4)
        basis = (f"{action.action_type} tends to relieve "
                 f"{pressure_key or 'no specific pressure'} "
                 f"(level={round(level, 3)}, evidence={round(evidence, 3)})")
        # Do not overclaim: if evidence is weak, cap expected gain.
        if evidence < 0.25:
            expected = min(expected, 0.1)
            basis += "; weak evidence -> gain capped"
        return InformationGainEstimate(
            action_id=action.action_id, action_type=action.action_type,
            expected_gain=expected, confidence=confidence,
            uncertainty=uncertainty, basis=basis)

    def compare_actions(self, actions: List[SamplingAction],
                        context: Dict[str, Any],
                        ) -> List[InformationGainEstimate]:
        estimates = [self.estimate_action(a, context) for a in actions]
        return sorted(estimates, key=lambda e: e.expected_gain, reverse=True)

    def score_observed_result(self, action: SamplingAction, result: Any,
                              before_context: Dict[str, Any],
                              after_context: Dict[str, Any],
                              ) -> float:
        """Observed gain proxy = measured reduction across key uncertainties."""
        before, after = dict(before_context or {}), dict(after_context or {})
        deltas = []
        # Reductions are positive gains.
        deltas.append(_num(before, "mysterium_pressure")
                      - _num(after, "mysterium_pressure"))
        deltas.append(_num(before, "prediction_error")
                      - _num(after, "prediction_error"))
        wm_b = before.get("world_model") or {}
        wm_a = after.get("world_model") or {}
        deltas.append(_num(wm_a, "prediction_accuracy")
                      - _num(wm_b, "prediction_accuracy"))
        proto_b = before.get("proto_language") or {}
        proto_a = after.get("proto_language") or {}
        cb = _num(proto_b, "symbol_count")
        ca = _num(proto_a, "symbol_count")
        if cb > 0 and ca > 0:
            deltas.append(_num(proto_b, "ambiguous_symbol_count") / cb
                          - _num(proto_a, "ambiguous_symbol_count") / ca)
        observed = round(max(-1.0, min(1.0, sum(deltas))), 4)
        self.history.append({
            "action_id": action.action_id,
            "action_type": action.action_type,
            "observed_gain": observed,
            "expected_gain": float(action.expected_information_gain)})
        self.history = self.history[-500:]
        return observed

    # -- helpers ------------------------------------------------------------------

    def _pressure_level(self, key: str, ctx: Dict[str, Any]) -> float:
        if not key:
            return 0.2
        if key == "world_model_uncertainty":
            wm = ctx.get("world_model") or {}
            nodes = _num(wm, "graph_node_count")
            acc = wm.get("prediction_accuracy")
            level = (1.0 - float(acc)) if acc is not None else 0.5
            if nodes > 0:
                level = max(level, _num(wm, "unknown_node_count") / nodes)
            return min(1.0, level)
        if key == "proto_symbol_ambiguity":
            proto = ctx.get("proto_language") or {}
            count = _num(proto, "symbol_count")
            return (min(1.0, _num(proto, "ambiguous_symbol_count") / count)
                    if count > 0 else 0.0)
        if key == "developmental_stagnation":
            return 1.0 if ctx.get("stagnation_status") in (
                "stagnating", "inert") else 0.1
        if key == "overstimulation":
            return min(1.0, _num(ctx, "novelty_rate")
                       + _num((ctx.get("ecology") or {}), "anomaly_rate"))
        if key == "memory_pressure":
            return _num(ctx, "memory_pressure")
        if key == "fatigue":
            return _num(ctx, "fatigue")
        return min(1.0, _num(ctx, key))

    def _evidence_strength(self, ctx: Dict[str, Any]) -> float:
        present = sum(1 for k in ("mysterium_pressure", "world_model",
                                  "proto_language", "prediction_error",
                                  "ecology")
                      if ctx.get(k) not in (None, {}, 0))
        return min(1.0, present / 4.0)

    def snapshot(self) -> Dict[str, Any]:
        if not self.history:
            return {"scored_actions": 0, "mean_observed_gain": None}
        gains = [h["observed_gain"] for h in self.history]
        return {
            "scored_actions": len(self.history),
            "mean_observed_gain": round(sum(gains) / len(gains), 4),
            "recent": self.history[-5:],
        }
