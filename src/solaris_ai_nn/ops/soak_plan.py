"""Soak plans -- staged escalation toward long runs, never auto-launched.

A plan is a document, not a command: it describes the stages (5-minute
simulated soak up to a 30-day soak), which safety checks apply, and which
stages require explicit flags. Generating a plan never starts anything.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Union

STANDARD_CHECKS = [
    "health monitor at every supervision interval",
    "watchdog heartbeat/checkpoint staleness checks",
    "resource budget (steps, artifacts, trace, atoms)",
    "artifact rotation (dry-run first)",
    "incident logging",
    "safe shutdown on critical health",
    "run registry entry",
]


@dataclass
class SoakStage:
    """One stage of the escalation ladder."""

    name: str
    description: str
    duration_s: float
    approx_steps: int
    requires_flag: bool
    included: bool
    auto_launch: bool = False  # NEVER True; stages are launched by operators
    safety_checks: List[str] = field(default_factory=lambda: list(STANDARD_CHECKS))

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SoakPlan:
    """The staged plan document."""

    stages: List[SoakStage] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    note: str = ("This plan is documentation. No stage is launched "
                 "automatically; long stages require explicit flags and an "
                 "operator decision after reviewing the previous stage.")

    def included_stages(self) -> List[SoakStage]:
        return [s for s in self.stages if s.included]

    def to_dict(self) -> Dict[str, Any]:
        return {"created_at": self.created_at, "note": self.note,
                "stages": [s.to_dict() for s in self.stages]}

    def to_markdown(self) -> str:
        lines = ["# Solaris-AI-NN staged soak plan", "", self.note, ""]
        for i, s in enumerate(self.stages, 1):
            status = "INCLUDED" if s.included else (
                "requires explicit flag" if s.requires_flag else "planned")
            lines.append(f"## Stage {i}: {s.name} ({status})")
            lines.append(f"- duration: {s.duration_s:.0f}s "
                         f"(~{s.approx_steps} steps)")
            lines.append(f"- {s.description}")
            lines.append("- safety checks:")
            lines.extend(f"  - {c}" for c in s.safety_checks)
            lines.append("")
        return "\n".join(lines)

    def write(self, output_dir: Union[str, Path]) -> Dict[str, str]:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        json_path = out / "soak_plan.json"
        md_path = out / "soak_plan.md"
        json_path.write_text(json.dumps(self.to_dict(), indent=2),
                             encoding="utf-8")
        md_path.write_text(self.to_markdown(), encoding="utf-8")
        return {"json": str(json_path), "markdown": str(md_path)}


@dataclass
class SoakPlanBuilder:
    """Builds the standard five-stage ladder."""

    include_24h: bool = False
    include_30d: bool = False
    steps_per_second_estimate: float = 500.0

    def build(self) -> SoakPlan:
        sps = self.steps_per_second_estimate

        def stage(name, desc, seconds, requires, included) -> SoakStage:
            return SoakStage(name=name, description=desc, duration_s=seconds,
                             approx_steps=int(seconds * sps),
                             requires_flag=requires, included=included)

        return SoakPlan(stages=[
            stage("5-minute simulated soak",
                  "bounded supervised run; validates the full ops loop "
                  "(health, watchdog, budget, rotation, registry).",
                  300.0, requires=False, included=True),
            stage("1-hour planned soak",
                  "first real-duration soak; run manually after stage 1 is "
                  "clean.", 3600.0, requires=False, included=False),
            stage("24-hour soak",
                  "requires soak_acknowledged + --include-24h; review stage 2 "
                  "incidents first.", 24 * 3600.0, requires=True,
                  included=self.include_24h),
            stage("7-day soak",
                  "requires explicit flag; verify artifact rotation and budget "
                  "headroom from the 24h run.", 7 * 24 * 3600.0, requires=True,
                  included=False),
            stage("30-day soak",
                  "requires soak_acknowledged + --include-30d; the long-horizon "
                  "continuity experiment.", 30 * 24 * 3600.0, requires=True,
                  included=self.include_30d),
        ])
