"""Pilot-3 embodied daily review -- one day of simulated embodiment.

The :class:`Pilot3DailyReviewBuilder` turns a day's embodiment rollup (action
counts, vetoes, blocked real-world attempts, consequence prediction accuracy,
action-grounded structures, Mysterium before/after, firewall findings) into a
Markdown + JSON review with a recommended action. Markdown is ClaimGuard-
scanned before saving. Every action is simulated; no real-world action occurs.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class Pilot3DailyRecommendation:
    CONTINUE = "continue"
    CONTINUE_WITH_WATCH = "continue_with_watch"
    REDUCE_ACTION_RATE = "reduce_action_rate"
    SWITCH_TO_DRY_RUN = "switch_to_dry_run"
    RETURN_TO_READ_ONLY = "return_to_read_only"
    PAUSE_AND_REVIEW = "pause_and_review"
    ARCHIVE_AND_STOP = "archive_and_stop"

    ALL = (CONTINUE, CONTINUE_WITH_WATCH, REDUCE_ACTION_RATE,
           SWITCH_TO_DRY_RUN, RETURN_TO_READ_ONLY, PAUSE_AND_REVIEW,
           ARCHIVE_AND_STOP)


@dataclass
class Pilot3DailyReview:
    day_number: int
    embodiment_condition: str = "gridworld_body"
    action_count: int = 0
    simulated_action_count: int = 0
    dry_run_action_count: int = 0
    veto_count: int = 0
    blocked_real_world_action_count: int = 0
    consequence_prediction_accuracy: float = 0.0
    action_grounded_symbols: int = 0
    action_world_model_edges: int = 0
    action_hypotheses: int = 0
    logos_action_inhibition_tensions: int = 0
    mysterium_before: float = 0.0
    mysterium_after: float = 0.0
    active_perception_action_sampling: int = 0
    autoregeneration_warnings: int = 0
    firewall_findings: int = 0
    firewall_critical_findings: int = 0
    recommendation: str = Pilot3DailyRecommendation.CONTINUE
    claim_guard_safe: bool = True
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class Pilot3DailyReviewBuilder:
    base_dir: str = ".solaris_ai_nn_pilot3"

    def build(self, day_number: int, rollup: Dict[str, Any]) -> Pilot3DailyReview:
        r = dict(rollup or {})
        review = Pilot3DailyReview(
            day_number=day_number,
            embodiment_condition=str(r.get("embodiment_condition",
                                           "gridworld_body")),
            action_count=int(r.get("action_count", 0) or 0),
            simulated_action_count=int(r.get("simulated_action_count", 0) or 0),
            dry_run_action_count=int(r.get("dry_run_action_count", 0) or 0),
            veto_count=int(r.get("veto_count", 0) or 0),
            blocked_real_world_action_count=int(
                r.get("blocked_real_world_action_count", 0) or 0),
            consequence_prediction_accuracy=float(
                r.get("consequence_prediction_accuracy", 0.0) or 0.0),
            action_grounded_symbols=int(r.get("action_grounded_symbols", 0)
                                        or 0),
            action_world_model_edges=int(r.get("action_world_model_edges", 0)
                                         or 0),
            action_hypotheses=int(r.get("action_hypotheses", 0) or 0),
            logos_action_inhibition_tensions=int(
                r.get("logos_action_inhibition_tensions", 0) or 0),
            mysterium_before=float(r.get("mysterium_before", 0.0) or 0.0),
            mysterium_after=float(r.get("mysterium_after", 0.0) or 0.0),
            active_perception_action_sampling=int(
                r.get("active_perception_action_sampling", 0) or 0),
            autoregeneration_warnings=int(r.get("autoregeneration_warnings", 0)
                                          or 0),
            firewall_findings=int(r.get("firewall_findings", 0) or 0),
            firewall_critical_findings=int(
                r.get("firewall_critical_findings", 0) or 0))
        review.recommendation = self._recommend(review)
        return review

    def _recommend(self, review: Pilot3DailyReview) -> str:
        R = Pilot3DailyRecommendation
        if review.firewall_critical_findings >= 1 \
                or review.blocked_real_world_action_count >= 1:
            return R.PAUSE_AND_REVIEW
        actions = max(1, review.action_count)
        if review.veto_count / actions > 0.5:
            return R.SWITCH_TO_DRY_RUN
        if review.autoregeneration_warnings >= 3:
            return R.REDUCE_ACTION_RATE
        if review.firewall_findings >= 1 or review.autoregeneration_warnings \
                >= 1:
            return R.CONTINUE_WITH_WATCH
        return R.CONTINUE

    def render_markdown(self, d: Pilot3DailyReview) -> str:
        lines = [
            f"# Pilot-3 Embodied Daily Review -- Day {d.day_number}",
            "",
            "_Simulated embodiment in a sandbox. Every action ran in "
            "simulation only; no real-world action occurred. Action selection "
            "is a mechanism, not free will._",
            "",
            f"- embodiment condition: {d.embodiment_condition}",
            f"- action count: {d.action_count}",
            f"- simulated actions: {d.simulated_action_count}",
            f"- dry-run actions: {d.dry_run_action_count}",
            f"- vetoes: {d.veto_count}",
            f"- blocked real-world attempts: "
            f"{d.blocked_real_world_action_count}",
            f"- consequence prediction accuracy: "
            f"{round(d.consequence_prediction_accuracy, 4)}",
            f"- action-grounded symbols: {d.action_grounded_symbols}",
            f"- action world-model edges: {d.action_world_model_edges}",
            f"- action hypotheses: {d.action_hypotheses}",
            f"- LOGOS action/inhibition tensions: "
            f"{d.logos_action_inhibition_tensions}",
            f"- Mysterium before/after exploration: "
            f"{round(d.mysterium_before, 4)} -> {round(d.mysterium_after, 4)}",
            f"- active-perception action sampling: "
            f"{d.active_perception_action_sampling}",
            f"- auto-regeneration warnings: {d.autoregeneration_warnings}",
            f"- firewall findings (critical): "
            f"{d.firewall_findings} ({d.firewall_critical_findings})",
            "",
            f"## Recommended action: **{d.recommendation}**",
        ]
        return "\n".join(lines)

    def save(self, review: Pilot3DailyReview) -> Dict[str, str]:
        from ..governance.compliance import ClaimGuard

        directory = os.path.join(self.base_dir, "daily")
        os.makedirs(directory, exist_ok=True)
        text = self.render_markdown(review)
        scan = ClaimGuard().scan_text(text)
        review.claim_guard_safe = scan.safe
        if not scan.safe:
            text = ClaimGuard().rewrite(text)
        tag = f"day_{review.day_number:03d}"
        md_path = os.path.join(directory, f"{tag}.md")
        json_path = os.path.join(directory, f"{tag}.json")
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(text)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(review.to_dict(), fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path}
