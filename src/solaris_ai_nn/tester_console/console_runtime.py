"""Tester console runtime -- bounded, read-only, static dashboard generator.

:class:`TesterConsoleRuntime` discovers local artifacts read-only, builds the status
model, summary cards, run index, safety panel, and next actions, then generates the
static Markdown dashboard (and optional offline HTML) plus the console report. It writes
only its own console files; it never modifies run artifacts, starts feeders, runs a
server, opens a browser, accesses the network/shell/Git/GitHub, controls hardware,
publishes/uploads, executes artifact contents, trains on tester feedback, or makes
unsupported claims.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .artifact_discovery import ConsoleArtifactDiscovery
from .console_profile import get_console_profile
from .dashboard_builder import TesterDashboardBuilder
from .next_actions import NextActionBuilder
from .run_index import RunIndexBuilder
from .safety import TesterConsoleSafetyValidator
from .safety_panel import SafetyPanelBuilder
from .status_model import StatusModelBuilder
from .summary_cards import SummaryCardBuilder


@dataclass
class TesterConsoleRuntime:
    """Bounded, read-only, static tester console runtime."""

    state_dir: str = ".solaris_ai_nn_live"
    tester_state_dir: str = ".solaris_ai_nn_tester"
    console_dir: str = ".solaris_ai_nn_tester/console"
    alpha_state_dir: str = ".solaris_ai_nn_alpha"
    docs_dir: str = ".solaris_ai_nn_docs"
    claims_dir: str = ".solaris_ai_nn_claims"
    profile: Optional[str] = None
    max_runtime_s: float = 60.0
    strict: bool = False
    dry_run: bool = False
    report_only: bool = False
    markdown_only: bool = False
    html: bool = True
    include_private_payloads: bool = False
    require_claimguard: bool = False

    safety: TesterConsoleSafetyValidator = field(
        default_factory=TesterConsoleSafetyValidator, init=False)
    console_profile: Any = field(default=None, init=False)
    run_id: str = field(default="", init=False)
    discovery: Any = field(default=None, init=False)
    status: Any = field(default=None, init=False)
    cards: List[Any] = field(default_factory=list, init=False)
    safety_panel: Any = field(default=None, init=False)
    run_index: Any = field(default=None, init=False)
    next_actions: List[Any] = field(default_factory=list, init=False)
    dashboard: Any = field(default=None, init=False)
    generated_files: Dict[str, Any] = field(default_factory=dict, init=False)
    reports: Dict[str, Any] = field(default_factory=dict, init=False)
    warnings: List[str] = field(default_factory=list, init=False)
    _refused: bool = field(default=False, init=False)

    _SUBDIRS = ("index", "pages", "assets", "reports", "runs", "safety")

    def __post_init__(self) -> None:
        self.console_profile = get_console_profile(self.profile)
        if self.markdown_only:
            self.html = False
        self.html = self.html and self.console_profile.emit_html
        # Private payloads are never displayed regardless of the requested flag.
        self.include_private_payloads = False
        self.run_id = f"console_{int(time.time() * 1000)}"
        if not self.max_runtime_s:
            self._refused = True

    def initialize(self) -> Dict[str, Any]:
        created = []
        for sub in self._SUBDIRS:
            path = os.path.join(self.console_dir, sub)
            existed = os.path.isdir(path)
            os.makedirs(path, exist_ok=True)
            created.append({"name": sub, "existed": existed})
        return {"console_dir": self.console_dir, "directories": created,
                "deletes_state": False, "modifies_run_artifacts": False}

    def run_doctor(self) -> Dict[str, Any]:
        bounded = self.safety.validate_bounded(self.max_runtime_s).safe
        return {"console_profile": self.console_profile.profile_id,
                "bounded": bounded, "read_only": True, "runs_server": False,
                "opens_browser": False, "passed": bounded,
                "note": "console doctor validates the profile + bounded runtime; "
                        "the console is read-only and runs no server"}

    def run(self) -> Dict[str, Any]:
        if self._refused or not self.safety.validate_bounded(
                self.max_runtime_s).safe:
            return {"refused": True, "reason": "unbounded runtime"}
        self.initialize()

        # 1. Read-only discovery.
        self.discovery = ConsoleArtifactDiscovery(
            state_dir=self.state_dir, tester_state_dir=self.tester_state_dir,
            alpha_state_dir=self.alpha_state_dir, docs_dir=self.docs_dir,
            claims_dir=self.claims_dir).discover()
        self.warnings.extend(self.discovery.warnings)

        # 2. Safety panel (needed before the status model so blockers override).
        self.safety_panel = SafetyPanelBuilder().build(self.discovery)

        # 3. Status model.
        self.status = StatusModelBuilder().build(self.discovery,
                                                 self.safety_panel)

        # 4. Cards, run index, next actions.
        self.cards = SummaryCardBuilder().build(
            self.discovery, self.status, self.safety_panel)
        self.run_index = RunIndexBuilder().build(self.discovery)
        self.next_actions = NextActionBuilder().build(self.status,
                                                      self.safety_panel)

        # 5. Dashboard model.
        self.dashboard = TesterDashboardBuilder().build(
            discovery=self.discovery, status=self.status, cards=self.cards,
            safety_panel=self.safety_panel, run_index=self.run_index,
            next_actions=self.next_actions)

        if not self.dry_run:
            self._generate()

        if self.require_claimguard and not _claimguard_available():
            self.warnings.append("ClaimGuard required but unavailable")

        self._update_integrations()
        return self._result()

    def _generate(self) -> None:
        from .markdown_builder import TesterConsoleMarkdownBuilder
        from .reports import TesterConsoleReportBuilder

        RunIndexBuilder().write(self.run_index, self.console_dir)
        if self.console_profile.emit_markdown and not self.console_profile.is_status_only:
            md = TesterConsoleMarkdownBuilder(
                dashboard=self.dashboard, safety_panel=self.safety_panel,
                run_index=self.run_index, next_actions=self.next_actions)
            self.generated_files["markdown"] = md.write(self.console_dir)
        if self.html:
            from .html_builder import TesterConsoleHtmlBuilder
            self.generated_files["html"] = TesterConsoleHtmlBuilder(
                dashboard=self.dashboard,
                safety_panel=self.safety_panel).write(self.console_dir)
        self.reports = TesterConsoleReportBuilder(self).write()

    def _update_integrations(self) -> None:
        try:
            from ..inner_map.model import InnerMapModel  # noqa: F401
            self._inner_map_record = self.inner_map_record()
        except Exception:
            self.warnings.append("inner map unavailable (record skipped)")

    # -- views --------------------------------------------------------------

    def console_status(self) -> Dict[str, Any]:
        status = self.status.to_dict() if self.status else {}
        sp = self.safety_panel.to_dict() if self.safety_panel else {}
        return {
            "console_available": True,
            "console_run_id": self.run_id,
            "console_profile": self.console_profile.profile_id,
            "read_only": True, "runs_server": False, "opens_browser": False,
            "overall_health": status.get("overall_health", "unknown"),
            "release_ready": status.get("release_ready", False),
            "artifact_count": len(self.discovery.artifacts)
            if self.discovery else 0,
            "missing_artifact_count": len(
                self.dashboard.sections["missing_artifacts"])
            if self.dashboard else 0,
            "blocker_count": status.get("blocker_count", 0)
            + sp.get("blocker_count", 0),
            "warning_count": status.get("warning_count", 0),
            "safety_status": sp.get("safety_status", "unknown"),
            "safety_block_count": sp.get("blocker_count", 0),
            "card_count": len(self.cards),
            "run_index_count": self.run_index.to_dict()["run_count"]
            if self.run_index else 0,
            "next_action_count": len(self.next_actions),
            "latest_next_action": self.next_actions[0].action
            if self.next_actions else "",
            "html_generated": "html" in self.generated_files,
            "markdown_generated": "markdown" in self.generated_files,
            "latest_console_index_path": self.generated_files.get(
                "markdown", {}).get("index") if isinstance(
                self.generated_files.get("markdown"), dict) else None,
            "latest_console_html_path": self.generated_files.get("html"),
            "console_safety_block_count": self.safety.rejected_count,
        }

    def snapshot(self) -> Dict[str, Any]:
        return self.console_status()

    def inner_map_record(self) -> Dict[str, Any]:
        st = self.console_status()
        return {
            "console_generated": True,
            "console_profile": st["console_profile"],
            "discovered_artifact_count": st["artifact_count"],
            "blocker_count": st["blocker_count"],
            "warning_count": st["warning_count"],
            "latest_console_index_path": st["latest_console_index_path"],
            "latest_console_html_path": st["latest_console_html_path"],
            "latest_next_action": st["latest_next_action"],
            "read_only": True,
        }

    def _run_summary(self) -> Dict[str, Any]:
        return {
            "console_run_id": self.run_id,
            "console_profile": self.console_profile.to_dict(),
            "console_status": self.console_status(),
            "discovery": self.discovery.to_dict() if self.discovery else {},
            "status_model": self.status.to_dict() if self.status else {},
            "safety_panel": self.safety_panel.to_dict()
            if self.safety_panel else {},
            "run_index": self.run_index.to_dict() if self.run_index else {},
            "next_actions": NextActionBuilder.to_dict(self.next_actions),
            "cards": [c.to_dict() for c in self.cards],
            "generated_files": self.generated_files,
            "warnings": list(self.warnings),
            "safety_status": self.safety.snapshot(),
        }

    def _result(self) -> Dict[str, Any]:
        st = self.console_status()
        return {
            "refused": False, "run_id": self.run_id,
            "console_profile": self.console_profile.profile_id,
            "overall_health": st["overall_health"],
            "blocker_count": st["blocker_count"],
            "warning_count": st["warning_count"],
            "safety_status": st["safety_status"],
            "artifact_count": st["artifact_count"],
            "missing_artifact_count": st["missing_artifact_count"],
            "latest_console_index_path": st["latest_console_index_path"],
            "latest_console_html_path": st["latest_console_html_path"],
            "latest_next_action": st["latest_next_action"],
            "generated_files": self.generated_files,
        }


def _claimguard_available() -> bool:
    try:
        from ..governance.compliance import ClaimGuard  # noqa: F401
        return True
    except Exception:
        return False
