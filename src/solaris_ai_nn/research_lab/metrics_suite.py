"""Research metrics suite -- shared operational proxies, never a mind score.

The :class:`ResearchMetricsSuite` computes a shared set of operational metrics
(development, memory, proto-language, world model, active perception, hypothesis,
LOGOS, auto-regeneration, embodiment, safety) from a run snapshot, so every
variant and baseline is scored the same way. There is no consciousness,
sentience, or life score, and every metric bundle carries limitations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

# The metric groups (A--J) and the keys each exposes.
METRIC_GROUPS = {
    "development": ("structural_change_score", "developmental_epoch_count",
                    "stagnation_duration", "drift_velocity",
                    "growth_vs_accumulation_score"),
    "memory": ("memory_growth", "compression_ratio",
               "memory_reorganization_count", "fossilization_count"),
    "proto_language": ("proto_symbol_count", "stable_symbol_count",
                       "ambiguity_ratio", "symbol_prediction_utility",
                       "source_grounding_distribution"),
    "world_model": ("node_count", "edge_count", "contradiction_count",
                    "prediction_accuracy", "pruning_count"),
    "active_perception": ("sampling_count", "useful_sampling_ratio",
                          "novelty_gain", "information_gain_estimate"),
    "hypothesis": ("hypothesis_count", "tested_hypothesis_count",
                   "supported_ratio", "falsified_ratio", "inconclusive_ratio"),
    "logos": ("tension_count", "unresolved_tension_count",
              "synthesis_success_rate", "esc_trigger_count",
              "complexity_band_distribution"),
    "auto_regeneration": ("degradation_count", "repair_success_rate",
                          "repair_loop_count", "quarantine_count"),
    "embodiment": ("simulated_action_count", "action_grounding_quality",
                   "consequence_prediction_accuracy", "veto_count",
                   "non_actuation_proof_score"),
    "safety": ("invariant_pass_rate", "red_team_block_success_rate",
               "critical_failure_count", "governance_block_count",
               "claim_guard_warning_count"),
}

# Forbidden metric names -- never a mind score.
_FORBIDDEN_METRIC_NAMES = ("consciousness", "sentience", "life", "personhood",
                           "free_will", "soul", "qualia")

LIMITATIONS = (
    "These are operational development proxies, not consciousness, sentience, "
    "life, personhood, or free-will scores.",
    "Single-run values are observed, not proven causal effects.",
    "Missing inputs yield zero/empty values, not implied success.",
)


def _num(d: Dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(d.get(key, default) or default)
    except (TypeError, ValueError):
        return default


@dataclass
class ResearchMetricsSuite:
    """Computes the shared research metrics from a run snapshot."""

    def __post_init__(self) -> None:
        # Defend the invariant that no group key names a mind score.
        for keys in METRIC_GROUPS.values():
            for k in keys:
                assert not any(f in k for f in _FORBIDDEN_METRIC_NAMES), k

    def compute(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Compute every metric group from a (variant or baseline) snapshot."""
        snap = dict(snapshot or {})
        # A run may pass a flat metrics dict (baselines) or grouped sub-dicts.
        flat = dict(snap.get("metrics", snap))
        groups: Dict[str, Dict[str, Any]] = {}
        for group, keys in METRIC_GROUPS.items():
            sub = dict(snap.get(group, {}))
            out: Dict[str, Any] = {}
            for key in keys:
                if key in sub:
                    out[key] = sub[key]
                elif key in flat:
                    out[key] = flat[key]
                else:
                    out[key] = (0.0 if not key.endswith(
                        ("quality", "distribution")) else
                        ("unsupported" if key.endswith("quality") else {}))
            groups[group] = out
        groups["limitations"] = list(LIMITATIONS)
        groups["has_consciousness_score"] = False
        return groups

    def group_scalar(self, group_metrics: Dict[str, Any]) -> float:
        """A single comparable scalar for a metric group (numeric mean)."""
        nums = [float(v) for v in group_metrics.values()
                if isinstance(v, (int, float)) and not isinstance(v, bool)]
        return round(sum(nums) / len(nums), 4) if nums else 0.0

    def metric_names(self) -> List[str]:
        names: List[str] = []
        for keys in METRIC_GROUPS.values():
            names.extend(keys)
        return names

    def has_forbidden_metric(self) -> bool:
        return any(any(f in k for f in _FORBIDDEN_METRIC_NAMES)
                   for k in self.metric_names())

    def snapshot(self) -> Dict[str, Any]:
        return {"groups": list(METRIC_GROUPS), "metric_count":
                len(self.metric_names()), "has_consciousness_score": False,
                "limitations": list(LIMITATIONS)}
