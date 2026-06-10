"""OperationalStatus -- everything an operator needs, in one snapshot."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..language.reporting import ExperimentReportBuilder


@dataclass
class OperationalStatus:
    """Aggregated operational state of one supervised run."""

    manifest: Dict[str, Any] = field(default_factory=dict)
    lifecycle: Optional[Dict[str, Any]] = None
    telemetry: Optional[Dict[str, Any]] = None
    health: Optional[Dict[str, Any]] = None
    watchdog: Optional[Dict[str, Any]] = None
    budget: Optional[Dict[str, Any]] = None
    incidents: List[Dict[str, Any]] = field(default_factory=list)
    artifacts: Optional[Dict[str, Any]] = None
    scorecard: Optional[Dict[str, Any]] = None
    inner_map_summary: Optional[Dict[str, Any]] = None
    language_summary: Optional[Dict[str, Any]] = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "manifest": self.manifest,
            "lifecycle": self.lifecycle,
            "telemetry": self.telemetry,
            "health": self.health,
            "watchdog": self.watchdog,
            "budget": self.budget,
            "incidents": list(self.incidents),
            "incident_count": len(self.incidents),
            "artifacts": self.artifacts,
            "scorecard": self.scorecard,
            "inner_map_summary": self.inner_map_summary,
            "language_summary": self.language_summary,
        }

    def to_markdown(self) -> str:
        builder = (ExperimentReportBuilder(title="Operational status")
                   .add_metadata(
                       run_id=self.manifest.get("run_id"),
                       mode=self.manifest.get("mode"),
                       safety_mode=self.manifest.get("safety_mode"),
                       health=(self.health or {}).get("level", "unknown"))
                   .add_section("runtime", {
                       "steps": (self.telemetry or {}).get("steps"),
                       "lifetime_steps": (self.telemetry or {}).get(
                           "lifetime_steps"),
                       "operator_notes": self.manifest.get("operator_notes")
                       or "none",
                   })
                   .add_section("health", self.health)
                   .add_section("watchdog", self.watchdog)
                   .add_section("budget", (self.budget or {}).get(
                       "last_report"))
                   .add_section("incidents", self.incidents[-5:]
                                or ["none recorded"])
                   .add_section("scorecard", self.scorecard)
                   .add_section("inner_map", self.inner_map_summary)
                   .add_section("artifacts", self.artifacts))
        if self.budget and (self.budget.get("last_report") or {}).get(
                "violations"):
            builder.add_limitation(
                "Budget violations occurred; see the budget section.")
        return builder.build().to_markdown()

    def compact_line(self) -> str:
        """One status line for terminals/logs."""
        health = (self.health or {}).get("level", "unknown")
        steps = (self.telemetry or {}).get("lifetime_steps",
                                           (self.telemetry or {}).get("steps", 0))
        stop = (self.watchdog or {}).get("stop_requested", False)
        return (f"[{self.manifest.get('run_id', '?')}] "
                f"mode={self.manifest.get('mode', '?')} health={health} "
                f"steps={steps} incidents={len(self.incidents)} "
                f"stop_requested={stop}")
