"""StructuralSummarizer -- counting and aggregation, never generation.

Summaries are purely structural: counts, dominants, means, and extremes drawn
from traces, telemetry, and snapshots. No LLM, no embeddings, no prose built
on hidden assumptions -- every number in a summary is computable from its
inputs alone.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .schemas import ExperimentReport, ExplanationContext, MeaningTrace


@dataclass
class StructuralSummarizer:
    """Aggregates runtime data into compact structural summaries."""

    def summarize_trace(self, trace: MeaningTrace) -> Dict[str, Any]:
        """Counts by category/predicate + dominant labels for a meaning trace."""
        categories = Counter(a.category for a in trace.atoms)
        predicates = Counter(a.predicate for a in trace.atoms)
        absence = sum(1 for a in trace.atoms
                      if "absence" in str(a.subject).lower())
        return {
            "atom_count": len(trace.atoms),
            "by_category": dict(categories),
            "by_predicate": dict(predicates),
            "dominant_category": (categories.most_common(1)[0][0]
                                  if categories else None),
            "dominant_predicate": (predicates.most_common(1)[0][0]
                                   if predicates else None),
            "absence_count": absence,
            "unknown_statements": categories.get("unknown", 0),
        }

    def summarize_session(self, context: ExplanationContext) -> Dict[str, Any]:
        """Structural session summary from an explanation context."""
        telemetry = context.telemetry or {}
        bridge = context.bridge or {}
        habits = sorted(context.habits, key=lambda h: abs(h.get("weight", 0.0)),
                        reverse=True)
        out: Dict[str, Any] = {
            "signals": {
                "events": telemetry.get("events", 0),
                "reservoir_updates": telemetry.get("reservoir_updates", 0),
                "readout_updates": telemetry.get("readout_updates", 0),
                "recent_prediction_error":
                    telemetry.get("recent_prediction_error", 0.0),
            },
            "substrate": {
                "type": bridge.get("substrate_type"),
                "state_norm": bridge.get("substrate_state_norm"),
                "activity_rate": bridge.get("substrate_activity_rate"),
            },
            "strongest_habits": habits[:3],
            "habit_pathways": bridge.get("habit_pathways", 0),
            "plasticity": {
                "applied": (context.plasticity or {}).get("applied_count", 0),
                "rejected": (context.plasticity or {}).get("rejected_count", 0),
            },
            "pruning": context.pruning or {"passes": 0, "removed": 0},
            "continuity": context.continuity
                or (context.inner_map or {}).get("continuity"),
        }
        if context.embodiment:
            emb = context.embodiment
            out["embodiment"] = {
                "position": emb.get("position"),
                "energy": emb.get("energy"),
                "exhausted": emb.get("exhausted"),
                "last_action": emb.get("last_action"),
                "action_authority": emb.get("action_authority"),
            }
        if context.trace_summary:
            out["meaning_trace"] = context.trace_summary
        return out

    def summarize_inner_map(self, inner_map: Dict[str, Any]) -> Dict[str, Any]:
        """Compact Inner MAP digest."""
        neural = inner_map.get("neural", {}) or {}
        plasticity = inner_map.get("plasticity", {}) or {}
        continuity = inner_map.get("continuity", {}) or {}
        return {
            "substrate_type": neural.get("substrate_type"),
            "state_norm": neural.get("reservoir_state_norm"),
            "habit_pathways": plasticity.get("habit_pathways"),
            "pruning_count": plasticity.get("pruning_count"),
            "lifetime_steps": continuity.get("lifetime_steps"),
            "restart_count": continuity.get("restart_count"),
            "embodiment_present": inner_map.get("embodiment") is not None,
            "integration_present": inner_map.get("integration") is not None,
        }

    def summarize_experiment(self, report_data: Dict[str, Any],
                             title: str = "Solaris-AI-NN experiment") -> ExperimentReport:
        """Wrap raw experiment data into an ExperimentReport with limitations."""
        return ExperimentReport(
            title=title,
            metadata={"generated_by": "StructuralSummarizer",
                      "deterministic": True},
            sections=dict(report_data),
            limitations=STANDARD_LIMITATIONS.copy(),
        )


# Every report carries these; honesty is structural, not optional.
STANDARD_LIMITATIONS: List[str] = [
    "Causal links are heuristic reconstructions from recorded order; "
    "confidence below 1.0 means association, not proven causation.",
    "Explanations are deterministic renderings of recorded state; the system "
    "reports 'does not know' where data is absent.",
    "Meaning traces are bounded; old atoms are dropped beyond capacity.",
    "Nothing in this report implies consciousness, intent, or experience -- "
    "'suggested' and 'tendency' name mechanisms, not desires.",
]
