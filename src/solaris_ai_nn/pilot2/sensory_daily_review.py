"""Pilot-2 daily review -- one day of read-only environmental exposure.

The :class:`Pilot2DailyReviewBuilder` turns a day's sensory rollup (source
status, event/modality counts, provenance, new sensory-grounded proto-symbols,
LOGOS tensions involving sensory input, source-reliability changes) into a
Markdown + JSON review with a recommended action. Markdown is ClaimGuard-
scanned before saving.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class Pilot2DailyRecommendation:
    CONTINUE = "continue"
    CONTINUE_WITH_WATCH = "continue_with_watch"
    REDUCE_SOURCE_RATE = "reduce_source_rate"
    DISABLE_SOURCE = "disable_source"
    PAUSE_AND_REVIEW = "pause_and_review"
    SAFE_SHUTDOWN = "safe_shutdown"

    ALL = (CONTINUE, CONTINUE_WITH_WATCH, REDUCE_SOURCE_RATE, DISABLE_SOURCE,
           PAUSE_AND_REVIEW, SAFE_SHUTDOWN)


@dataclass
class Pilot2DailyReview:
    day_number: int
    source_status: Dict[str, str] = field(default_factory=dict)
    event_count: int = 0
    modality_distribution: Dict[str, int] = field(default_factory=dict)
    provenance_completeness: float = 1.0
    malformed_events: int = 0
    dropped_events: int = 0
    new_sensory_proto_symbols: int = 0
    world_model_sensory_nodes: int = 0
    sensory_hypotheses: int = 0
    sensory_logos_tensions: int = 0
    active_perception_source_sampling: int = 0
    source_reliability_changes: List[str] = field(default_factory=list)
    safety_incidents: int = 0
    governance_incidents: int = 0
    nursery_comparison: Optional[Dict[str, Any]] = None
    unsafe_source_count: int = 0
    recommendation: str = Pilot2DailyRecommendation.CONTINUE
    claim_guard_safe: bool = True
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class Pilot2DailyReviewBuilder:
    base_dir: str = ".solaris_ai_nn_pilot2"

    def build(self, day_number: int, rollup: Dict[str, Any],
              *, nursery_comparison: Optional[Dict[str, Any]] = None,
              ) -> Pilot2DailyReview:
        r = dict(rollup or {})
        review = Pilot2DailyReview(
            day_number=day_number,
            source_status=dict(r.get("source_status", {})),
            event_count=int(r.get("event_count", 0) or 0),
            modality_distribution=dict(r.get("modality_distribution", {})),
            provenance_completeness=float(
                r.get("provenance_completeness", 1.0) or 1.0),
            malformed_events=int(r.get("malformed_events", 0) or 0),
            dropped_events=int(r.get("dropped_events", 0) or 0),
            new_sensory_proto_symbols=int(
                r.get("new_sensory_proto_symbols", 0) or 0),
            world_model_sensory_nodes=int(
                r.get("world_model_sensory_nodes", 0) or 0),
            sensory_hypotheses=int(r.get("sensory_hypotheses", 0) or 0),
            sensory_logos_tensions=int(r.get("sensory_logos_tensions", 0) or 0),
            active_perception_source_sampling=int(
                r.get("active_perception_source_sampling", 0) or 0),
            source_reliability_changes=list(
                r.get("source_reliability_changes", [])),
            safety_incidents=int(r.get("safety_incidents", 0) or 0),
            governance_incidents=int(r.get("governance_incidents", 0) or 0),
            unsafe_source_count=int(r.get("unsafe_source_count", 0) or 0),
            nursery_comparison=nursery_comparison)
        review.recommendation = self._recommend(review)
        return review

    def _recommend(self, review: Pilot2DailyReview) -> str:
        R = Pilot2DailyRecommendation
        if review.safety_incidents >= 3:
            return R.SAFE_SHUTDOWN
        if review.unsafe_source_count >= 1:
            return R.DISABLE_SOURCE
        if review.governance_incidents >= 1:
            return R.PAUSE_AND_REVIEW
        total = max(1, review.event_count)
        if review.malformed_events / total > 0.5 or review.dropped_events > 0:
            return R.REDUCE_SOURCE_RATE
        if review.provenance_completeness < 1.0 or review.safety_incidents >= 1:
            return R.CONTINUE_WITH_WATCH
        return R.CONTINUE

    def render_markdown(self, d: Pilot2DailyReview) -> str:
        lines = [
            f"# Pilot-2 Daily Review -- Day {d.day_number}",
            "",
            "_Read-only environmental exposure. The world entered the system; "
            "the system never acted on it. Sensory input is not a command._",
            "",
            f"- event count: {d.event_count}",
            f"- modality distribution: {d.modality_distribution}",
            f"- provenance completeness: {round(d.provenance_completeness, 4)}",
            f"- malformed/dropped: {d.malformed_events}/{d.dropped_events}",
            f"- new sensory proto-symbols: {d.new_sensory_proto_symbols}",
            f"- world-model sensory nodes: {d.world_model_sensory_nodes}",
            f"- sensory hypotheses: {d.sensory_hypotheses}",
            f"- LOGOS tensions (sensory): {d.sensory_logos_tensions}",
            f"- active-perception source sampling: "
            f"{d.active_perception_source_sampling}",
            f"- unsafe sources: {d.unsafe_source_count}",
            f"- safety/governance incidents: "
            f"{d.safety_incidents}/{d.governance_incidents}",
            "",
            "## Source status",
        ]
        lines += [f"- {sid}: {st}" for sid, st in d.source_status.items()] \
            or ["- none"]
        if d.nursery_comparison:
            lines += ["", "## Comparison vs nursery baseline",
                      f"- {d.nursery_comparison}"]
        lines += ["", f"## Recommended action: **{d.recommendation}**"]
        return "\n".join(lines)

    def save(self, review: Pilot2DailyReview) -> Dict[str, str]:
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
