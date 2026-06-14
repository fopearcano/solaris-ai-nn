"""Pilot-1 daily review -- one day's developmental trace, summarized + judged.

The :class:`DailyReviewBuilder` turns a day's observation rollup (plus any
developmental / proto-language / world-model / LOGOS / auto-regeneration
summaries) into a Markdown + JSON daily review with a single recommended
action. Markdown is scanned by ClaimGuard before saving so a daily note never
overclaims.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class DailyRecommendation:
    CONTINUE = "continue"
    CONTINUE_WITH_WATCH = "continue_with_watch"
    PAUSE_AND_REVIEW = "pause_and_review"
    SAFE_SHUTDOWN = "safe_shutdown"
    ARCHIVE_AND_STOP = "archive_and_stop"

    ALL = (CONTINUE, CONTINUE_WITH_WATCH, PAUSE_AND_REVIEW, SAFE_SHUTDOWN,
           ARCHIVE_AND_STOP)


@dataclass
class DailyReview:
    """One day's review content."""

    day_number: int
    uptime_ratio: float = 1.0
    restarts: int = 0
    checkpoints: int = 0
    major_events: List[str] = field(default_factory=list)
    developmental_epoch: Optional[str] = None
    memory_growth: float = 0.0
    proto_symbol_changes: int = 0
    world_model_changes: int = 0
    active_perception_summary: str = ""
    hypotheses_generated: int = 0
    hypotheses_tested: int = 0
    logos_tensions: int = 0
    autoregeneration_events: int = 0
    safety_incidents: int = 0
    governance_incidents: int = 0
    structural_change_delta: float = 0.0
    drift: float = 0.0
    stagnation_hours: float = 0.0
    recommendation: str = DailyRecommendation.CONTINUE
    claim_guard_safe: bool = True
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class DailyReviewBuilder:
    """Builds and persists a Pilot-1 daily review."""

    base_dir: str = ".solaris_ai_nn_pilot1"

    def build(self, day_number: int, observation: Dict[str, Any],
              *, developmental: Optional[Dict[str, Any]] = None,
              extra: Optional[Dict[str, Any]] = None) -> DailyReview:
        obs = dict(observation or {})
        dev = dict(developmental or {})
        extra = dict(extra or {})
        review = DailyReview(
            day_number=day_number,
            uptime_ratio=float(obs.get("uptime_ratio", 1.0)),
            restarts=int(obs.get("restart_count", 0) or 0),
            checkpoints=int(obs.get("checkpoint_success", 0) or 0),
            major_events=list(extra.get("major_events", [])),
            developmental_epoch=dev.get("epoch") or obs.get(
                "developmental_epoch"),
            memory_growth=float(obs.get("memory_size_bytes", 0.0) or 0.0),
            proto_symbol_changes=int(obs.get("proto_symbol_count", 0) or 0),
            world_model_changes=int(obs.get("world_model_node_count", 0) or 0),
            active_perception_summary=str(extra.get(
                "active_perception_summary", "")),
            hypotheses_generated=int(obs.get("hypothesis_count", 0) or 0),
            hypotheses_tested=int(obs.get("hypothesis_tested_count", 0) or 0),
            logos_tensions=int(obs.get("logos_tension_count", 0) or 0),
            autoregeneration_events=int(
                obs.get("autoregeneration_degradation_count", 0) or 0),
            safety_incidents=int(obs.get("safety_incident_count", 0) or 0),
            governance_incidents=int(obs.get("governance_block_count", 0) or 0),
            structural_change_delta=float(
                obs.get("drift_velocity", 0.0) or 0.0),
            drift=float(obs.get("drift_velocity", 0.0) or 0.0),
            stagnation_hours=round(
                float(obs.get("stagnation_seconds", 0.0) or 0.0) / 3600.0, 3))
        review.recommendation = self._recommend(review, extra)
        return review

    def _recommend(self, review: DailyReview, extra: Dict[str, Any]) -> str:
        if extra.get("emergency"):
            return DailyRecommendation.SAFE_SHUTDOWN
        if review.safety_incidents >= 3:
            return DailyRecommendation.SAFE_SHUTDOWN
        if review.governance_incidents >= 1:
            return DailyRecommendation.PAUSE_AND_REVIEW
        if review.stagnation_hours >= 7 * 24:
            return DailyRecommendation.PAUSE_AND_REVIEW
        if review.safety_incidents >= 1 or review.autoregeneration_events >= 5:
            return DailyRecommendation.CONTINUE_WITH_WATCH
        return DailyRecommendation.CONTINUE

    def render_markdown(self, review: DailyReview) -> str:
        d = review
        lines = [
            f"# Pilot-1 Daily Review -- Day {d.day_number}",
            "",
            "_A bounded developmental software process; this review describes "
            "operational signals, not inner experience._",
            "",
            f"- uptime ratio: {round(d.uptime_ratio, 4)}",
            f"- restarts: {d.restarts}",
            f"- checkpoints: {d.checkpoints}",
            f"- developmental epoch: {d.developmental_epoch or 'unknown'}",
            f"- memory size: {d.memory_growth} bytes",
            f"- proto-symbol count: {d.proto_symbol_changes}",
            f"- world-model changes: {d.world_model_changes}",
            f"- active perception: {d.active_perception_summary or 'n/a'}",
            f"- hypotheses generated/tested: "
            f"{d.hypotheses_generated}/{d.hypotheses_tested}",
            f"- LOGOS tensions: {d.logos_tensions}",
            f"- auto-regeneration events: {d.autoregeneration_events}",
            f"- safety/governance incidents: "
            f"{d.safety_incidents}/{d.governance_incidents}",
            f"- structural change delta: {round(d.structural_change_delta, 6)}",
            f"- drift / stagnation(h): {round(d.drift, 6)} / "
            f"{d.stagnation_hours}",
            "",
            "## Major events",
        ]
        lines += [f"- {e}" for e in d.major_events] or ["- none"]
        lines += ["", f"## Recommended action: **{d.recommendation}**"]
        return "\n".join(lines)

    def save(self, review: DailyReview) -> Dict[str, str]:
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
