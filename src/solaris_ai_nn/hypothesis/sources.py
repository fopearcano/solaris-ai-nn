"""Hypothesis sources -- where uncertainty turns into a seed.

The :class:`HypothesisSourceScanner` reads a normalized context (Mysterium,
prediction misses, weak world-model edges, causal candidates, ambiguous
proto-symbols, failed proto-syntax rules, delayed-consequence groups,
recurring anomalies, stagnation, active-perception uncertainty targets,
executive inhibition, homeostasis conflicts, boundary events, developmental
phase-transition candidates) and emits :class:`HypothesisSeed`s. Seeds are
not hypotheses; they carry evidence refs and are marked offline when their
source is counterfactual/offline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .hypotheses import HypothesisType


def _num(d: Optional[Dict[str, Any]], key: str, default: float = 0.0) -> float:
    try:
        return float((d or {}).get(key, default) or 0.0)
    except (TypeError, ValueError):
        return default


@dataclass
class HypothesisSeed:
    """A pre-hypothesis: a source of uncertainty worth a candidate."""

    source: str
    hypothesis_type: str
    target_ref: Optional[str] = None
    observation: str = ""
    intensity: float = 0.0  # [0, 1] -- how strongly the source points here
    evidence_refs: List[str] = field(default_factory=list)
    offline: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class HypothesisSourceScanner:
    """Scans context for hypothesis seeds. Deterministic."""

    last_seeds: List[HypothesisSeed] = field(default_factory=list, init=False)

    def scan(self, context: Dict[str, Any]) -> List[HypothesisSeed]:
        ctx = dict(context or {})
        seeds: List[HypothesisSeed] = []

        def add(source, htype, target, observation, intensity, refs,
                offline=False, **meta):
            if intensity > 0.0 and refs:
                seeds.append(HypothesisSeed(
                    source=source, hypothesis_type=htype, target_ref=target,
                    observation=observation, intensity=round(intensity, 4),
                    evidence_refs=list(refs), offline=offline, metadata=meta))

        # 1. High Mysterium pressure.
        mysterium = _num(ctx, "mysterium_pressure")
        add("mysterium", HypothesisType.MYSTERIUM_REDUCTION, "unknown",
            "unresolved unknown pressure may fall with targeted sampling",
            mysterium, ["mysterium_pressure"])

        # 2. Repeated prediction misses.
        pred_error = _num(ctx, "prediction_error")
        add("prediction_miss", HypothesisType.PREDICTION, "prediction",
            "a recurring pattern may predict its consequence",
            min(1.0, pred_error), ["prediction_error"])

        # 3. Weak world-model edges + 4. causal candidates.
        wm = ctx.get("world_model") or {}
        for edge in (wm.get("weak_edges") or [])[:3]:
            ref = edge if isinstance(edge, str) else str(edge)
            add("weak_world_edge", HypothesisType.WORLD_MODEL_EDGE, ref,
                "this world-model edge may be weak or false", 0.6,
                [f"weak_edge:{ref}"])
        for cand in (wm.get("causal_candidates") or [])[:3]:
            ref = cand if isinstance(cand, str) else str(cand)
            add("causal_candidate", HypothesisType.CAUSAL_CANDIDATE, ref,
                "this association candidate may be a causal candidate", 0.55,
                [f"causal_candidate:{ref}"])
        low_conf = wm.get("low_confidence_nodes") or []
        if low_conf:
            add("world_unknown", HypothesisType.WORLD_MODEL_EDGE,
                str(low_conf[0]),
                "this low-confidence region may become clearer if sampled",
                0.5, [f"node:{low_conf[0]}"])

        # 5. Ambiguous proto-symbols + 6. failed proto-syntax rules.
        proto = ctx.get("proto_language") or {}
        for sym in (proto.get("ambiguous_symbols") or [])[:3]:
            add("ambiguous_symbol", HypothesisType.PROTO_SYMBOL_GROUNDING,
                str(sym),
                "this proto-symbol may refer to two different patterns",
                0.55, [f"symbol:{sym}"])
        for rule in (proto.get("failed_syntax_rules") or [])[:3]:
            add("failed_syntax", HypothesisType.PROTO_SYNTAX, str(rule),
                "this proto-syntax regularity may not hold on new traces",
                0.5, [f"rule:{rule}"])

        # 7. Delayed-consequence groups.
        ecology = ctx.get("ecology") or {}
        groups = ecology.get("delayed_groups") or []
        if not groups and _num(ecology, "delayed_consequence_group_count") > 0:
            groups = [f"DLY_{i}" for i in range(int(_num(
                ecology, "delayed_consequence_group_count")))][:2]
        for group in groups[:3]:
            gref = group.get("group_id") if isinstance(group, dict) else group
            add("delayed_group", HypothesisType.DELAYED_CONSEQUENCE, str(gref),
                "this delayed consequence may belong to an earlier signal",
                0.55, [f"delay_group:{gref}"])

        # 8. Recurring anomalies.
        anomaly_rate = _num(ecology, "anomaly_rate")
        if anomaly_rate > 0.05 or ecology.get("recurring_anomalies"):
            add("anomaly", HypothesisType.ANOMALY_PATTERN, "anomaly",
                "this anomaly may be recurring, not noise",
                min(1.0, max(0.4, anomaly_rate * 3.0)), ["anomaly_rate"])

        # 9. Stagnation detector.
        if ctx.get("stagnation_status") in ("stagnating", "inert"):
            add("stagnation", HypothesisType.STAGNATION_RECOVERY, "stagnation",
                "novelty sampling during stagnation may raise structural "
                "change", 0.5, ["stagnation_status"])

        # 10. Active-perception uncertainty targets.
        for tgt in (ctx.get("uncertainty_targets") or [])[:3]:
            ref = tgt.get("target_ref") if isinstance(tgt, dict) else str(tgt)
            add("active_perception", HypothesisType.PREDICTION, str(ref),
                "this uncertain area may become clearer if sampled", 0.45,
                [f"uncertainty:{ref}"])

        # 11. Executive repeated inhibition.
        executive = ctx.get("executive") or {}
        if _num(executive, "inhibited_candidate_count") >= 5:
            add("executive_inhibition", HypothesisType.EXECUTIVE_ARBITRATION,
                "inhibition_pattern",
                "this candidate may be inhibited only in one context", 0.4,
                ["inhibited_candidate_count"])

        # 12. Homeostasis conflict patterns.
        homeostasis = ctx.get("homeostasis") or {}
        if _num(homeostasis, "conflict_count") >= 1:
            add("homeostasis_conflict",
                HypothesisType.HOMEOSTATIC_REGULATION,
                homeostasis.get("dominant_need", "need"),
                "this need conflict may resolve toward one stable channel",
                0.4, ["conflict_count"])

        # 13. Boundary events.
        if _num(ctx, "boundary_event_count") >= 1 \
                or ctx.get("boundary_events"):
            add("boundary", HypothesisType.BOUNDARY, "boundary",
                "boundary events near a context may predict executive "
                "inhibition", 0.4, ["boundary_events"])

        # 14. Developmental phase-transition candidates.
        if _num(ctx, "phase_transition_candidates") >= 1:
            add("phase_transition", HypothesisType.PREDICTION,
                "phase_transition",
                "a sudden metric move may recur under similar conditions",
                0.4, ["phase_transition_candidates"])

        # Habit-context (when habit info is present).
        if ctx.get("habit_context"):
            add("habit", HypothesisType.HABIT_CONTEXT,
                str(ctx["habit_context"]),
                "this habit may be useful only in one context", 0.4,
                ["habit_context"])

        self.last_seeds = seeds
        return seeds

    def rank_seeds(self, seeds: List[HypothesisSeed],
                   ) -> List[HypothesisSeed]:
        return sorted(seeds, key=lambda s: s.intensity, reverse=True)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "seed_count": len(self.last_seeds),
            "by_type": self._counts(),
            "recent": [s.to_dict() for s in self.last_seeds[:5]],
        }

    def _counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for seed in self.last_seeds:
            counts[seed.hypothesis_type] = counts.get(
                seed.hypothesis_type, 0) + 1
        return counts
