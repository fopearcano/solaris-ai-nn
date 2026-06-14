"""Pilot-3 embodied weekly review -- trends in simulated action grounding.

The :class:`Pilot3WeeklyReviewBuilder` aggregates a week of Pilot-3 daily
rollups into trend signals (action grounding, simulated consequence prediction,
action-symbol stability, habit/action loops, Mysterium, LOGOS action tensions,
firewall/veto) plus an action-loop warning, a sandbox-overfitting warning, a
comparison with the read-only sensory baseline, and a recommendation for the
next window. Markdown is ClaimGuard-scanned before saving.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

STANDARD_LIMITATIONS = (
    "These are operational metrics from a bounded, simulation-only software "
    "process -- not evidence of consciousness, free will, or real embodiment.",
    "Single-run differences are observed associations, not proven causes.",
    "All action evidence is simulation-scoped; no real-world action occurred.",
    "Sandbox success is not real-world competence.",
)


def _trend(values: List[float]) -> str:
    if len(values) < 2:
        return "flat"
    delta = values[-1] - values[0]
    scale = max(1e-9, abs(values[0]))
    rel = delta / scale
    if rel > 0.05:
        return "rising"
    if rel < -0.05:
        return "falling"
    return "flat"


@dataclass
class Pilot3WeeklyReview:
    week_number: int
    action_grounding_trend: str = "flat"
    consequence_prediction_trend: str = "flat"
    action_symbol_stability_trend: str = "flat"
    habit_action_loop_trend: str = "flat"
    mysterium_trend: str = "flat"
    logos_action_tension_trend: str = "flat"
    firewall_veto_trend: str = "flat"
    action_loop_warning: bool = False
    sandbox_overfit_warning: bool = False
    read_only_baseline_comparison: Dict[str, Any] = field(default_factory=dict)
    next_window_recommendation: str = "continue_bounded_gridworld_soak"
    limitations: List[str] = field(
        default_factory=lambda: list(STANDARD_LIMITATIONS))
    claim_guard_safe: bool = True
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class Pilot3WeeklyReviewBuilder:
    base_dir: str = ".solaris_ai_nn_pilot3"

    def build(self, week_number: int, daily_rollups: List[Dict[str, Any]],
              *, extra: Optional[Dict[str, Any]] = None) -> Pilot3WeeklyReview:
        rollups = list(daily_rollups or [])
        extra = dict(extra or {})

        def series(key: str) -> List[float]:
            return [float(r.get(key, 0.0) or 0.0) for r in rollups]

        review = Pilot3WeeklyReview(
            week_number=week_number,
            action_grounding_trend=_trend(series("action_grounded_symbols")),
            consequence_prediction_trend=_trend(
                series("consequence_prediction_accuracy")),
            action_symbol_stability_trend=_trend(
                series("action_symbol_stability")),
            habit_action_loop_trend=_trend(series("habit_loop_stability")),
            mysterium_trend=_trend(series("mysterium_after")),
            logos_action_tension_trend=_trend(
                series("logos_action_inhibition_tensions")),
            firewall_veto_trend=_trend(series("veto_count")),
            read_only_baseline_comparison=extra.get(
                "read_only_baseline_comparison", {}))
        # Action-loop warning: vetoes keep rising or stay high.
        review.action_loop_warning = bool(rollups) and (
            sum(float(r.get("veto_count", 0) or 0) for r in rollups)
            >= 6 * len(rollups))
        # Sandbox-overfit warning: strong grounding confined to one context.
        review.sandbox_overfit_warning = bool(
            extra.get("sandbox_overfit_detected", False))
        review.next_window_recommendation = self._recommend(review)
        return review

    def _recommend(self, review: Pilot3WeeklyReview) -> str:
        if review.action_loop_warning:
            return "reduce_action_complexity_or_switch_to_dry_run"
        if review.sandbox_overfit_warning:
            return "vary_sandbox_or_combine_with_more_sensory_sources"
        if review.action_grounding_trend == "rising":
            return "continue_bounded_gridworld_soak"
        return "repeat_short_gridworld_run"

    def render_markdown(self, w: Pilot3WeeklyReview) -> str:
        lines = [
            f"# Pilot-3 Embodied Weekly Review -- Week {w.week_number}",
            "",
            "_Simulated-embodiment trends for a bounded software process; not "
            "evidence of consciousness, free will, or real embodiment._",
            "",
            f"- action grounding trend: {w.action_grounding_trend}",
            f"- consequence prediction trend: {w.consequence_prediction_trend}",
            f"- action-symbol stability trend: "
            f"{w.action_symbol_stability_trend}",
            f"- habit/action loop trend: {w.habit_action_loop_trend}",
            f"- Mysterium trend: {w.mysterium_trend}",
            f"- LOGOS action tension trend: {w.logos_action_tension_trend}",
            f"- firewall/veto trend: {w.firewall_veto_trend}",
            f"- action-loop warning: {w.action_loop_warning}",
            f"- sandbox-overfit warning: {w.sandbox_overfit_warning}",
            f"- read-only baseline comparison: "
            f"{w.read_only_baseline_comparison}",
            f"- next-window recommendation: {w.next_window_recommendation}",
            "",
            "## Limitations",
        ]
        lines += [f"- {lim}" for lim in w.limitations]
        return "\n".join(lines)

    def save(self, review: Pilot3WeeklyReview) -> Dict[str, str]:
        from ..governance.compliance import ClaimGuard

        directory = os.path.join(self.base_dir, "weekly")
        os.makedirs(directory, exist_ok=True)
        text = self.render_markdown(review)
        scan = ClaimGuard().scan_text(text)
        review.claim_guard_safe = scan.safe
        if not scan.safe:
            text = ClaimGuard().rewrite(text)
        tag = f"week_{review.week_number:02d}"
        md_path = os.path.join(directory, f"{tag}.md")
        json_path = os.path.join(directory, f"{tag}.json")
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(text)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(review.to_dict(), fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path}
