"""Pilot-1 weekly review -- trends across a week, with honest limitations.

The :class:`WeeklyReviewBuilder` aggregates a week of daily rollups into
trend signals (structural growth, memory compression, Mysterium,
proto-language, world model, hypothesis evidence, LOGOS complexity bands,
auto-regeneration success/failure) and a recommendation for the next week. It
always includes a limitations section and surfaces stagnation/regression
warnings. Markdown is ClaimGuard-scanned before saving.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

STANDARD_LIMITATIONS = (
    "These are operational metrics from a bounded software process, not "
    "evidence of consciousness, understanding, or feeling.",
    "Trends over one week are short; structural claims need the full pilot "
    "trace and baseline comparison.",
    "Simulated-time slices are not real-time evidence and are labelled as "
    "such.",
)


@dataclass
class WeeklyReview:
    """One week's trend review content."""

    week_number: int
    uptime_ratio: float = 1.0
    module_stability: str = "unknown"
    structural_growth_trend: str = "flat"
    memory_compression_trend: str = "flat"
    mysterium_trend: str = "flat"
    proto_language_trend: str = "flat"
    world_model_trend: str = "flat"
    active_perception_usefulness: str = "unknown"
    hypothesis_evidence_trend: str = "flat"
    logos_complexity_band_distribution: Dict[str, int] = field(
        default_factory=dict)
    autoregeneration_success: int = 0
    autoregeneration_failure: int = 0
    safety_summary: str = "no critical incidents"
    governance_summary: str = "no blocks"
    phase_transition_candidates: List[str] = field(default_factory=list)
    stagnation_warning: bool = False
    regression_warning: bool = False
    recommendation: str = "continue"
    limitations: List[str] = field(default_factory=lambda: list(
        STANDARD_LIMITATIONS))
    claim_guard_safe: bool = True
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


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
class WeeklyReviewBuilder:
    """Builds and persists a Pilot-1 weekly review."""

    base_dir: str = ".solaris_ai_nn_pilot1"

    def build(self, week_number: int, daily_rollups: List[Dict[str, Any]],
              *, extra: Optional[Dict[str, Any]] = None) -> WeeklyReview:
        rollups = list(daily_rollups or [])
        extra = dict(extra or {})

        def series(key: str) -> List[float]:
            return [float(r.get(key, 0.0) or 0.0) for r in rollups]

        structural = series("structural_change_score")
        memory = series("memory_size_bytes")
        mysterium = series("mysterium_pressure")
        proto = series("proto_symbol_count")
        world = series("world_model_node_count")
        hyp = series("hypothesis_count")
        uptimes = series("uptime_ratio") or [1.0]

        review = WeeklyReview(
            week_number=week_number,
            uptime_ratio=round(sum(uptimes) / max(1, len(uptimes)), 4),
            module_stability=extra.get("module_stability", "stable"),
            structural_growth_trend=_trend(structural),
            memory_compression_trend=_trend(memory),
            mysterium_trend=_trend(mysterium),
            proto_language_trend=_trend(proto),
            world_model_trend=_trend(world),
            active_perception_usefulness=extra.get(
                "active_perception_usefulness", "unknown"),
            hypothesis_evidence_trend=_trend(hyp),
            logos_complexity_band_distribution=extra.get(
                "logos_complexity_band_distribution", {}),
            autoregeneration_success=int(extra.get(
                "autoregeneration_success", 0)),
            autoregeneration_failure=int(extra.get(
                "autoregeneration_failure", 0)),
            safety_summary=extra.get("safety_summary", "no critical incidents"),
            governance_summary=extra.get("governance_summary", "no blocks"),
            phase_transition_candidates=list(extra.get(
                "phase_transition_candidates", [])))
        review.stagnation_warning = (review.structural_growth_trend == "flat"
                                     and review.proto_language_trend == "flat")
        review.regression_warning = review.structural_growth_trend == "falling"
        review.recommendation = self._recommend(review)
        return review

    def _recommend(self, review: WeeklyReview) -> str:
        if review.regression_warning:
            return "pause_and_review"
        if review.stagnation_warning:
            return "continue_with_watch"
        return "continue"

    def render_markdown(self, review: WeeklyReview) -> str:
        w = review
        bands = ", ".join(f"{k}={v}" for k, v in
                          w.logos_complexity_band_distribution.items()) or "n/a"
        lines = [
            f"# Pilot-1 Weekly Review -- Week {w.week_number}",
            "",
            "_Operational trends for a bounded software process; not evidence "
            "of consciousness or understanding._",
            "",
            f"- uptime ratio: {w.uptime_ratio}",
            f"- module stability: {w.module_stability}",
            f"- structural growth trend: {w.structural_growth_trend}",
            f"- memory compression trend: {w.memory_compression_trend}",
            f"- Mysterium trend: {w.mysterium_trend}",
            f"- proto-language trend: {w.proto_language_trend}",
            f"- world-model trend: {w.world_model_trend}",
            f"- active perception usefulness: {w.active_perception_usefulness}",
            f"- hypothesis evidence trend: {w.hypothesis_evidence_trend}",
            f"- LOGOS complexity bands: {bands}",
            f"- auto-regeneration success/failure: "
            f"{w.autoregeneration_success}/{w.autoregeneration_failure}",
            f"- safety: {w.safety_summary}",
            f"- governance: {w.governance_summary}",
            f"- phase-transition candidates: "
            f"{', '.join(w.phase_transition_candidates) or 'none'}",
            f"- stagnation warning: {w.stagnation_warning}",
            f"- regression warning: {w.regression_warning}",
            "",
            f"## Recommendation for next week: **{w.recommendation}**",
            "",
            "## Limitations",
        ]
        lines += [f"- {lim}" for lim in w.limitations]
        return "\n".join(lines)

    def save(self, review: WeeklyReview) -> Dict[str, str]:
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
