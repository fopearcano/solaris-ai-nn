"""Pilot-2 weekly review -- trends in source reliability and grounding.

The :class:`Pilot2WeeklyReviewBuilder` aggregates a week of Pilot-2 daily
rollups into trend signals (source reliability, grounding quality, sensory
proto-language / world-model trends, Mysterium response, overload/stagnation)
and an exposure-schedule recommendation for the next week, with honest
limitations. Markdown is ClaimGuard-scanned before saving.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

STANDARD_LIMITATIONS = (
    "These are operational metrics from a read-only, bounded software process "
    "-- not evidence of consciousness, understanding, or feeling.",
    "Single-run differences are observed associations, not proven causes.",
    "Simulated/fixture exposure is not real-time evidence and is labelled so.",
    "Grounding is operational association; input text is not meaning.",
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
class Pilot2WeeklyReview:
    week_number: int
    source_reliability_trend: str = "flat"
    grounding_quality_trend: str = "flat"
    proto_language_sensory_trend: str = "flat"
    world_model_sensory_trend: str = "flat"
    mysterium_response: str = "flat"
    comparison_arm_summary: Dict[str, Any] = field(default_factory=dict)
    overload_signal: bool = False
    stagnation_signal: bool = False
    memory_growth: float = 0.0
    provenance_growth: float = 0.0
    source_curation_recommendation: str = "keep_current_sources"
    next_week_exposure_recommendation: str = "continue_alternating_schedule"
    limitations: List[str] = field(
        default_factory=lambda: list(STANDARD_LIMITATIONS))
    claim_guard_safe: bool = True
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class Pilot2WeeklyReviewBuilder:
    base_dir: str = ".solaris_ai_nn_pilot2"

    def build(self, week_number: int, daily_rollups: List[Dict[str, Any]],
              *, extra: Optional[Dict[str, Any]] = None) -> Pilot2WeeklyReview:
        rollups = list(daily_rollups or [])
        extra = dict(extra or {})

        def series(key: str) -> List[float]:
            return [float(r.get(key, 0.0) or 0.0) for r in rollups]

        review = Pilot2WeeklyReview(
            week_number=week_number,
            source_reliability_trend=_trend(series("reliable_source_count")),
            grounding_quality_trend=_trend(series("grounding_score")),
            proto_language_sensory_trend=_trend(
                series("new_sensory_proto_symbols")),
            world_model_sensory_trend=_trend(
                series("world_model_sensory_nodes")),
            mysterium_response=_trend(series("mysterium_pressure")),
            comparison_arm_summary=extra.get("comparison_arm_summary", {}),
            memory_growth=series("memory_size_bytes")[-1]
            if series("memory_size_bytes") else 0.0,
            provenance_growth=series("provenance_completeness")[-1]
            if series("provenance_completeness") else 1.0)
        review.overload_signal = any(
            float(r.get("malformed_events", 0) or 0) >
            0.5 * max(1, float(r.get("event_count", 1) or 1))
            for r in rollups)
        review.stagnation_signal = (review.grounding_quality_trend == "flat"
                                    and review.proto_language_sensory_trend
                                    == "flat")
        review.source_curation_recommendation = (
            "review_unsafe_or_noisy_sources" if review.overload_signal
            else "keep_current_sources")
        review.next_week_exposure_recommendation = (
            "increase_quiet_windows" if review.overload_signal
            else "increase_source_variety" if review.stagnation_signal
            else "continue_alternating_schedule")
        return review

    def render_markdown(self, w: Pilot2WeeklyReview) -> str:
        lines = [
            f"# Pilot-2 Weekly Review -- Week {w.week_number}",
            "",
            "_Read-only environmental exposure trends for a bounded software "
            "process; not evidence of consciousness or understanding._",
            "",
            f"- source reliability trend: {w.source_reliability_trend}",
            f"- grounding quality trend: {w.grounding_quality_trend}",
            f"- sensory proto-language trend: "
            f"{w.proto_language_sensory_trend}",
            f"- sensory world-model trend: {w.world_model_sensory_trend}",
            f"- Mysterium response: {w.mysterium_response}",
            f"- overload signal: {w.overload_signal}",
            f"- stagnation signal: {w.stagnation_signal}",
            f"- comparison arms: {w.comparison_arm_summary}",
            f"- source curation: {w.source_curation_recommendation}",
            f"- next-week exposure: {w.next_week_exposure_recommendation}",
            "",
            "## Limitations",
        ]
        lines += [f"- {lim}" for lim in w.limitations]
        return "\n".join(lines)

    def save(self, review: Pilot2WeeklyReview) -> Dict[str, str]:
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
