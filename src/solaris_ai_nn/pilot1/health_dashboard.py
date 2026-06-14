"""Pilot-1 health dashboard -- a text/Markdown/JSON snapshot of pilot health.

This is *not* a web dashboard. The :class:`PilotHealthDashboard` assembles the
current phase, runtime, uptime, module health, budgets, checkpoint status, and
the latest incident / auto-regeneration / LOGOS-Esc / safety signals into a
Markdown + JSON file an operator can read at a glance. It computes nothing it
cannot ground in the observation snapshot it is given.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PilotHealthState:
    """The fields a dashboard renders for one moment of a pilot."""

    pilot_phase: str = "unknown"
    pilot_mode: str = "plan_only"
    elapsed_seconds: float = 0.0
    target_duration_days: float = 0.0
    uptime_ratio: float = 1.0
    latest_heartbeat: Optional[float] = None
    module_health: str = "unknown"
    degraded_modules: List[str] = field(default_factory=list)
    memory_mb: Optional[float] = None
    disk_mb: float = 0.0
    disk_budget_mb: float = 0.0
    checkpoint_status: str = "unknown"
    latest_incident: Optional[str] = None
    latest_autoregeneration_signal: Optional[str] = None
    latest_logos_esc_state: Optional[str] = None
    latest_safety_block: Optional[str] = None
    developmental_epoch: Optional[str] = None
    ecology_regime: Optional[str] = None
    proto_symbol_count: int = 0
    structural_change_score: float = 0.0
    exit_recommendation: str = "continue"
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class PilotHealthDashboard:
    """Renders a pilot health state to dashboard.md and dashboard.json."""

    base_dir: str = ".solaris_ai_nn_pilot1"

    def build_state(self, *, protocol: Any = None, observability: Any = None,
                    resource: Any = None, failure_detector: Any = None,
                    config: Any = None,
                    extra: Optional[Dict[str, Any]] = None) -> PilotHealthState:
        extra = dict(extra or {})
        latest = {}
        if observability is not None:
            latest = observability.latest
        state = PilotHealthState()
        if config is not None:
            state.pilot_mode = config.mode
            state.target_duration_days = float(
                config.target_duration_days or 0.0)
            state.disk_budget_mb = float(getattr(config, "max_disk_mb", 0.0))
        if protocol is not None:
            snap = protocol.snapshot()
            state.pilot_phase = snap.get("current_phase", "unknown")
        if observability is not None:
            state.elapsed_seconds = observability.uptime_seconds()
            state.proto_symbol_count = int(
                latest.get("proto_symbol_count", 0) or 0)
            state.structural_change_score = float(
                latest.get("structural_change_score", 0.0) or 0.0)
            state.degraded_modules = extra.get("degraded_modules", [])
            state.latest_heartbeat = state.timestamp
        if resource is not None:
            rsnap = resource.snapshot()
            rlatest = rsnap.get("latest") or {}
            state.disk_mb = float(rlatest.get("total_mb", 0.0) or 0.0)
            state.memory_mb = rlatest.get("memory_hint_mb")
        if failure_detector is not None:
            fsnap = failure_detector.snapshot()
            state.exit_recommendation = fsnap.get("overall_recommendation",
                                                  "continue")
        # Overlay any explicit values the caller supplied.
        for key in ("uptime_ratio", "module_health", "degraded_modules",
                    "checkpoint_status", "latest_incident",
                    "latest_autoregeneration_signal", "latest_logos_esc_state",
                    "latest_safety_block", "developmental_epoch",
                    "ecology_regime", "exit_recommendation"):
            if key in extra:
                setattr(state, key, extra[key])
        return state

    def render_markdown(self, state: PilotHealthState) -> str:
        lines = [
            "# Pilot-1 Health Dashboard",
            "",
            "_A bounded, simulated/observed software process. Not a person; "
            "no real-world authority._",
            "",
            f"- current pilot phase: **{state.pilot_phase}**",
            f"- pilot mode: {state.pilot_mode}",
            f"- elapsed runtime: {round(state.elapsed_seconds / 3600.0, 3)} h",
            f"- target duration: {state.target_duration_days} days",
            f"- uptime ratio: {round(state.uptime_ratio, 4)}",
            f"- latest heartbeat: {state.latest_heartbeat}",
            f"- module health: {state.module_health}",
            f"- degraded modules: "
            f"{', '.join(state.degraded_modules) or 'none'}",
            f"- memory: {state.memory_mb if state.memory_mb is not None else 'unknown'} MB",
            f"- disk: {state.disk_mb} / {state.disk_budget_mb} MB",
            f"- checkpoint status: {state.checkpoint_status}",
            f"- latest incident: {state.latest_incident or 'none'}",
            f"- latest auto-regeneration signal: "
            f"{state.latest_autoregeneration_signal or 'none'}",
            f"- latest LOGOS Esc state: "
            f"{state.latest_logos_esc_state or 'none'}",
            f"- latest safety/governance block: "
            f"{state.latest_safety_block or 'none'}",
            f"- developmental epoch: {state.developmental_epoch or 'unknown'}",
            f"- ecology regime: {state.ecology_regime or 'unknown'}",
            f"- proto-symbol count: {state.proto_symbol_count}",
            f"- structural change score: "
            f"{round(state.structural_change_score, 6)}",
            f"- exit recommendation: **{state.exit_recommendation}**",
        ]
        return "\n".join(lines)

    def write(self, state: PilotHealthState) -> Dict[str, str]:
        os.makedirs(self.base_dir, exist_ok=True)
        md_path = os.path.join(self.base_dir, "dashboard.md")
        json_path = os.path.join(self.base_dir, "dashboard.json")
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(self.render_markdown(state))
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(state.to_dict(), fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path}
