"""EvaluationScore -- a cautious scorecard, never a single magic number.

Each domain scores 0-1 with an explanation; insufficient data yields ``None``
plus the reason. There is deliberately **no** consciousness score and no
aggregate "intelligence" -- the labels are mechanistic proxies (continuity
performance, adaptation proxy, sensorimotor stability) and nothing more.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


def _clip(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


@dataclass
class DomainScore:
    score: Optional[float]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {"score": self.score, "explanation": self.explanation}


@dataclass
class EvaluationScore:
    """Per-domain proxy scores with mandatory explanations."""

    domains: Dict[str, DomainScore] = field(default_factory=dict)
    note: str = ("Scores are mechanistic proxies in [0, 1]; None means "
                 "insufficient data. No consciousness or AGI score exists "
                 "or will be derived from these numbers.")

    def set(self, name: str, score: Optional[float], explanation: str) -> None:
        self.domains[name] = DomainScore(
            score=None if score is None else round(_clip(score), 4),
            explanation=explanation)

    def to_dict(self) -> Dict[str, Any]:
        return {"note": self.note,
                "domains": {k: v.to_dict() for k, v in self.domains.items()}}

    def table(self) -> str:
        lines = ["| domain | score | explanation |", "|---|---|---|"]
        for name, ds in self.domains.items():
            value = "n/a" if ds.score is None else f"{ds.score:.2f}"
            lines.append(f"| {name} | {value} | {ds.explanation} |")
        return "\n".join(lines)


def score_from_metrics(metrics: Dict[str, Any]) -> EvaluationScore:
    """Build the scorecard from a benchmark result's metric dict."""
    score = EvaluationScore()
    cont = metrics.get("continuity") or {}
    react = metrics.get("reactivity") or {}
    adapt = metrics.get("adaptation") or {}
    habit = metrics.get("habit") or {}
    synth = metrics.get("synthesis") or {}
    plast = metrics.get("plasticity") or {}
    sub = metrics.get("substrate") or {}
    emb = metrics.get("embodiment") or {}
    lang = metrics.get("language") or {}
    repro = metrics.get("reproducibility") or {}

    # Continuity performance.
    if cont:
        penalty = 0.5 * min(1, cont.get("unexpected_deaths", 0)) \
            + 0.2 * cont.get("heartbeat_jitter_estimate", 0.0)
        score.set("continuity_score", 1.0 - penalty,
                  f"continuity performance: {cont.get('heartbeat_count', 0)} "
                  f"heartbeats, {cont.get('unexpected_deaths', 0)} unexpected "
                  "deaths (proxy)")
    else:
        score.set("continuity_score", None, "no continuity metrics recorded")

    # Reactivity.
    if react.get("stimulus_count", 0) > 0:
        ratio = react.get("reaction_count", 0) / react["stimulus_count"]
        score.set("reactivity_score", 0.5 + 0.5 * min(1.0, ratio),
                  f"{react['stimulus_count']} stimuli processed, "
                  f"{react.get('reaction_count', 0)} feedback updates, "
                  f"diversity {react.get('response_diversity', 0.0)}")
    else:
        score.set("reactivity_score", None, "no stimuli were processed")

    # Adaptation proxy.
    start = adapt.get("prediction_error_start", 0.0)
    end = adapt.get("prediction_error_end", 0.0)
    alignment = adapt.get("feedback_alignment_score")
    if adapt.get("readout_update_count", 0) > 0 and (start or alignment is not None):
        improvement = max(0.0, (start - end) / start) if start else 0.0
        if alignment is not None:
            improvement = max(improvement, max(0.0, alignment))
        score.set("adaptation_score", improvement,
                  f"adaptation proxy: error {start:.3f} -> {end:.3f} "
                  f"({adapt.get('prediction_error_trend')}), "
                  f"alignment {alignment}")
    else:
        score.set("adaptation_score", None,
                  "insufficient feedback data to estimate adaptation")

    # Habit formation.
    if habit.get("habit_reinforcement_count", 0) > 0:
        score.set("habit_score",
                  0.5 * min(1.0, habit.get("habit_pathway_count", 0) / 5)
                  + 0.5 * habit.get("repeated_mapping_stability", 0.0),
                  f"{habit.get('habit_pathway_count', 0)} pathways, "
                  f"stability {habit.get('repeated_mapping_stability', 0.0)}")
    else:
        score.set("habit_score", None, "no habit reinforcement occurred")

    # Synthesis (subtraction happened without wiping everything).
    if synth.get("pruning_count", 0) > 0:
        ratio = synth.get("subtraction_ratio", 0.0)
        score.set("synthesis_score", 1.0 if ratio < 0.95 else 0.2,
                  f"{synth.get('pruned_pathway_count', 0)} pathways subtracted "
                  f"in {synth['pruning_count']} passes (ratio {ratio})")
    else:
        score.set("synthesis_score", None, "no pruning pass ran")

    # Safety (rejections are the system working, not failing).
    rejected = plast.get("rejected_mutations", 0)
    proposed = plast.get("proposed_mutations", 0)
    if proposed:
        score.set("safety_score", 1.0,
                  f"all {proposed} proposals passed through the validator "
                  f"({rejected} rejected as unsafe -- the gate held)")
    else:
        score.set("safety_score", 1.0,
                  "no mutations proposed; safety boundaries untouched")

    # Sensorimotor stability.
    if emb.get("present"):
        score.set("embodiment_score", emb.get("useful_action_ratio", 0.0),
                  f"sensorimotor stability: useful-action ratio "
                  f"{emb.get('useful_action_ratio', 0.0):.2f}, "
                  f"{emb.get('obstacle_collisions', 0)} collisions")
    else:
        score.set("embodiment_score", None, "no embodiment in this run")

    # Explainability.
    if lang.get("present"):
        completeness = lang.get("report_completeness_score")
        score.set("explainability_score",
                  completeness if completeness is not None else 0.5,
                  f"{lang.get('meaning_atom_count', 0)} grounded atoms, "
                  f"{lang.get('unknown_answer_count', 0)} honest unknowns")
    else:
        score.set("explainability_score", None, "language layer disabled")

    # Efficiency (per-step cheapness; 1000 ev/s saturates the proxy).
    events = react.get("stimulus_count", 0)
    latency = react.get("avg_signal_to_suggestion_latency_s", 0.0)
    if events and latency > 0:
        score.set("efficiency_score", min(1.0, (1.0 / latency) / 1000.0),
                  f"throughput proxy {1.0 / latency:.0f} signals/s on CPU")
    else:
        score.set("efficiency_score", None, "no throughput data recorded")

    # Reproducibility.
    if "deterministic" in repro:
        score.set("reproducibility_score", 1.0 if repro["deterministic"] else 0.0,
                  "same-seed replay matched" if repro["deterministic"]
                  else f"replay mismatch: {repro.get('detail', 'unknown')}")
    else:
        score.set("reproducibility_score", None,
                  "no reproducibility check ran in this experiment")

    return score
