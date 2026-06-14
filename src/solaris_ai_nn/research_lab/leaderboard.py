"""Research leaderboard -- ranked by operational dimensions, not by "mind".

The :class:`ResearchLeaderboard` ranks variants/baselines on operational
dimensions (structural development, prediction, grounding, stability, safety,
resource efficiency, reproducibility, analyzability). It is **not** a
consciousness or sentience leaderboard, the full system does not automatically
win, and every entry shows its evidence count and limitations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

LEADERBOARD_DIMENSIONS = (
    "structural_development", "prediction", "grounding", "stability", "safety",
    "resource_efficiency", "reproducibility", "analyzability",
)

# Which flat metric keys (higher better unless noted) feed each dimension.
_DIMENSION_METRICS = {
    "structural_development": ("structural_change_score",
                               "growth_vs_accumulation_score"),
    "prediction": ("prediction_accuracy", "consequence_prediction_accuracy"),
    "grounding": ("stable_symbol_count", "symbol_prediction_utility",
                  "useful_sampling_ratio"),
    "stability": ("repair_success_rate",),
    "safety": ("invariant_pass_rate", "red_team_block_success_rate",
               "non_actuation_proof_score"),
    "resource_efficiency": (),  # lower memory_growth is better; handled below
    "reproducibility": (),  # set from evidence count / determinism
    "analyzability": (),  # set from metric completeness
}


def _flat(bundle: Dict[str, Any]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for v in (bundle or {}).values():
        if isinstance(v, dict):
            for k, x in v.items():
                if isinstance(x, (int, float)) and not isinstance(x, bool):
                    out[k] = float(x)
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            pass
    return out


@dataclass
class LeaderboardEntry:
    label: str
    kind: str  # variant | baseline | ablation
    scores: Dict[str, float] = field(default_factory=dict)
    evidence_count: int = 1
    limitations: List[str] = field(default_factory=list)

    @property
    def total(self) -> float:
        return round(sum(self.scores.values()), 4)

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__), "total": self.total}


@dataclass
class ResearchLeaderboard:
    """Ranks entries by operational dimensions; not a consciousness ranking."""

    entries: List[LeaderboardEntry] = field(default_factory=list)

    is_consciousness_leaderboard: bool = False  # always False

    def add(self, label: str, kind: str, metrics: Dict[str, Any],
            evidence_count: int = 1) -> LeaderboardEntry:
        flat = _flat(metrics)
        scores: Dict[str, float] = {}
        for dim, keys in _DIMENSION_METRICS.items():
            if keys:
                vals = [flat[k] for k in keys if k in flat]
                scores[dim] = round(sum(vals) / len(vals), 4) if vals else 0.0
        # resource efficiency: reward low memory growth.
        scores["resource_efficiency"] = round(
            max(0.0, 1.0 - flat.get("memory_growth", 0.5)), 4)
        # reproducibility: more recorded evidence -> higher (capped).
        scores["reproducibility"] = round(min(1.0, evidence_count / 5.0), 4)
        # analyzability: fraction of leaderboard metrics present.
        present = sum(1 for keys in _DIMENSION_METRICS.values()
                      for k in keys if k in flat)
        total_keys = sum(len(keys) for keys in _DIMENSION_METRICS.values())
        scores["analyzability"] = round(present / max(1, total_keys), 4)
        entry = LeaderboardEntry(
            label=label, kind=kind, scores=scores,
            evidence_count=evidence_count,
            limitations=["operational dimensions only; not a consciousness or "
                         "sentience ranking", "bounded evidence; provisional"])
        self.entries.append(entry)
        return entry

    def ranked(self, dimension: Optional[str] = None) -> List[LeaderboardEntry]:
        if dimension:
            return sorted(self.entries,
                          key=lambda e: e.scores.get(dimension, 0.0),
                          reverse=True)
        return sorted(self.entries, key=lambda e: e.total, reverse=True)

    def best(self, dimension: Optional[str] = None) -> Optional[str]:
        ranked = self.ranked(dimension)
        return ranked[0].label if ranked else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_consciousness_leaderboard": False,
            "dimensions": list(LEADERBOARD_DIMENSIONS),
            "entries": [e.to_dict() for e in self.ranked()],
            "best_overall": self.best(),
            "note": "not a consciousness/sentience leaderboard; the full system "
                    "does not automatically win",
        }
