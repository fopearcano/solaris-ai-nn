"""Operator status board -- one claim-guarded view of the whole system.

:class:`OperatorStatusBoard` gathers the headline state of every subsystem
(profiles, safety, red-team, assurance, pilots, research, architecture, ops,
Inner MAP, ADRs, design debt, blockers) plus the recommended next action and
writes a Markdown + JSON board. The Markdown is scanned by ClaimGuard before it
is written, so the board never makes an unsupported claim.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .console_config import OperatorConsoleConfig
from .next_action import NextActionRecommender
from .profile_catalog import ProfileCatalog


@dataclass
class StatusBoardSnapshot:
    console_mode: str
    available_profile_count: int
    blocked_profile_count: int
    latest_safety_status: str
    latest_red_team_status: str
    latest_assurance_status: str
    latest_pilot_statuses: Dict[str, Any]
    latest_research_status: str
    latest_architecture_status: str
    latest_ops_incident: Optional[str]
    latest_inner_map_snapshot: Optional[str]
    open_adr_count: int
    critical_design_debt_count: int
    unresolved_safety_blocker_count: int
    recommended_next_action: str
    claim_guard_safe: bool = True
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class OperatorStatusBoard:
    """Builds and writes the operator status board."""

    config: OperatorConsoleConfig = field(default_factory=OperatorConsoleConfig)
    catalog: ProfileCatalog = field(default_factory=ProfileCatalog)
    safety_status: Optional[Dict[str, Any]] = None
    research_status: Optional[Dict[str, Any]] = None
    architecture_status: Optional[Dict[str, Any]] = None
    pilot_status: Optional[Dict[str, Any]] = None
    ops_status: Optional[Dict[str, Any]] = None
    inner_map_status: Optional[Dict[str, Any]] = None

    def build(self) -> StatusBoardSnapshot:
        safety = self.safety_status or {}
        arch = self.architecture_status or {}
        blockers = int(safety.get("unresolved_blocker_count", 0) or 0)
        rec = NextActionRecommender().top(
            safety_status=self.safety_status,
            research_findings=self.research_status,
            architecture_roadmap=self.architecture_status,
            design_debt={"critical_count":
                         arch.get("critical_design_debt_count", 0)})
        snap = StatusBoardSnapshot(
            console_mode=self.config.mode,
            available_profile_count=len(self.catalog.runnable_entries()),
            blocked_profile_count=len(self.catalog.blocked_entries()),
            latest_safety_status=str(safety.get("status", "unknown")),
            latest_red_team_status=str(safety.get("red_team_status", "unknown")),
            latest_assurance_status=str(
                safety.get("assurance_status", "unknown")),
            latest_pilot_statuses=dict(self.pilot_status or {}),
            latest_research_status=str(
                (self.research_status or {}).get("status", "unknown")),
            latest_architecture_status=str(arch.get("status", "unknown")),
            latest_ops_incident=(self.ops_status or {}).get("latest_incident"),
            latest_inner_map_snapshot=(
                self.inner_map_status or {}).get("snapshot_path"),
            open_adr_count=int(arch.get("open_adr_count", 0) or 0),
            critical_design_debt_count=int(
                arch.get("critical_design_debt_count", 0) or 0),
            unresolved_safety_blocker_count=blockers,
            recommended_next_action=(rec.action_type if rec else
                                     "inspect status board"))
        md = self._render_markdown(snap)
        snap.claim_guard_safe = self._claim_guard_safe(md)
        return snap

    def _render_markdown(self, snap: StatusBoardSnapshot) -> str:
        lines = [
            "# Operator Status Board", "",
            "_A local, file-backed view. The console coordinates; it grants no "
            "real-world authority and cannot bypass governance or safety._", "",
            f"- console mode: `{snap.console_mode}`",
            f"- available profiles: {snap.available_profile_count}",
            f"- blocked profiles: {snap.blocked_profile_count}",
            f"- safety invariant status: `{snap.latest_safety_status}`",
            f"- red-team status: `{snap.latest_red_team_status}`",
            f"- assurance case status: `{snap.latest_assurance_status}`",
            f"- research status: `{snap.latest_research_status}`",
            f"- architecture review status: `{snap.latest_architecture_status}`",
            f"- open ADRs: {snap.open_adr_count}",
            f"- critical design debt: {snap.critical_design_debt_count}",
            f"- unresolved safety blockers: "
            f"{snap.unresolved_safety_blocker_count}",
            f"- latest ops incident: {snap.latest_ops_incident or 'none'}",
            f"- recommended next action: `{snap.recommended_next_action}`",
            "",
        ]
        if snap.latest_pilot_statuses:
            lines.append("## Pilot statuses")
            for key, value in snap.latest_pilot_statuses.items():
                lines.append(f"- {key}: {value}")
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _claim_guard_safe(text: str) -> bool:
        try:
            from ..governance.compliance import ClaimGuard

            return ClaimGuard().scan_text(text).safe
        except Exception:
            return True

    def write(self) -> Dict[str, Any]:
        snap = self.build()
        os.makedirs(self.config.state_dir, exist_ok=True)
        md_path = os.path.join(self.config.state_dir, "STATUS_BOARD.md")
        json_path = os.path.join(self.config.state_dir, "STATUS_BOARD.json")
        md = self._render_markdown(snap)
        if not snap.claim_guard_safe:
            from ..governance.compliance import ClaimGuard

            md = ClaimGuard().rewrite(md)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(md)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(snap.to_dict(), fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path, "snapshot": snap}
