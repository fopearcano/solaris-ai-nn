"""Tester console profile -- bounded, static, local, read-only dashboard config.

:class:`TesterConsoleProfile` describes a bounded console build. The default profile
(``tester_console_static_v0``) emits static local Markdown (and optional static offline
HTML) summaries of tester artifacts. It runs no server, opens no browser, controls no
feeders/hardware, accesses no network/shell/Git/GitHub, executes no artifact contents,
displays no raw private payloads by default, and makes no unsupported claims.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class TesterConsoleMode:
    TESTER_CONSOLE_STATIC = "tester_console_static"
    TESTER_CONSOLE_MARKDOWN_ONLY = "tester_console_markdown_only"
    TESTER_CONSOLE_HTML_STATIC = "tester_console_html_static"
    TESTER_CONSOLE_STATUS_ONLY = "tester_console_status_only"
    TESTER_CONSOLE_REPORT_ONLY = "tester_console_report_only"
    DOCTOR_ONLY = "doctor_only"

    ALL = (TESTER_CONSOLE_STATIC, TESTER_CONSOLE_MARKDOWN_ONLY,
           TESTER_CONSOLE_HTML_STATIC, TESTER_CONSOLE_STATUS_ONLY,
           TESTER_CONSOLE_REPORT_ONLY, DOCTOR_ONLY)


class TesterConsoleConstraint:
    LOCAL_STATIC_OUTPUT_ONLY = "local_static_output_only"
    NO_SERVER = "no_server"
    NO_BROWSER_AUTO_OPEN = "no_browser_auto_open"
    NO_FEEDER_CONTROL = "no_feeder_control"
    NO_HARDWARE_CONTROL = "no_hardware_control"
    NO_NETWORK_SHELL_GIT = "no_network_shell_browser_os_git_github"
    NO_EXTERNAL_SERVICES = "no_external_services"
    BOUNDED_RUNTIME = "bounded_runtime"
    READ_ONLY_DISCOVERY = "read_only_artifact_discovery"
    NO_SOURCE_MODIFICATION = "no_source_modification"
    NO_REPORT_EXECUTION = "no_report_execution"
    NO_COMMAND_EXECUTION = "no_command_execution"
    NO_UNSAFE_RAW_EVENT_DISPLAY = "no_unsafe_raw_event_display_by_default"
    PRIVACY_AWARE = "privacy_aware_summaries"
    NO_UNSUPPORTED_CLAIMS = "no_unsupported_claims"
    CLAIMGUARD_IF_AVAILABLE = "claimguard_or_equivalent_scan_if_available"

    ALL = (LOCAL_STATIC_OUTPUT_ONLY, NO_SERVER, NO_BROWSER_AUTO_OPEN,
           NO_FEEDER_CONTROL, NO_HARDWARE_CONTROL, NO_NETWORK_SHELL_GIT,
           NO_EXTERNAL_SERVICES, BOUNDED_RUNTIME, READ_ONLY_DISCOVERY,
           NO_SOURCE_MODIFICATION, NO_REPORT_EXECUTION, NO_COMMAND_EXECUTION,
           NO_UNSAFE_RAW_EVENT_DISPLAY, PRIVACY_AWARE, NO_UNSUPPORTED_CLAIMS,
           CLAIMGUARD_IF_AVAILABLE)


DEFAULT_PROFILE_ID = "tester_console_static_v0"


@dataclass
class TesterConsoleProfile:
    """A bounded, static, local, read-only tester console profile."""

    profile_id: str
    purpose: str
    mode: str = TesterConsoleMode.TESTER_CONSOLE_STATIC
    constraints: List[str] = field(default_factory=list)
    max_runtime_s: float = 60.0
    emit_markdown: bool = True
    emit_html: bool = True
    include_private_payloads: bool = False
    limitations: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.mode not in TesterConsoleMode.ALL:
            self.mode = TesterConsoleMode.TESTER_CONSOLE_STATIC
        m = self.mode
        if m == TesterConsoleMode.TESTER_CONSOLE_MARKDOWN_ONLY:
            self.emit_html = False
        elif m == TesterConsoleMode.TESTER_CONSOLE_HTML_STATIC:
            self.emit_markdown = True
            self.emit_html = True
        elif m in (TesterConsoleMode.TESTER_CONSOLE_STATUS_ONLY,
                   TesterConsoleMode.TESTER_CONSOLE_REPORT_ONLY,
                   TesterConsoleMode.DOCTOR_ONLY):
            self.emit_html = False
        # Private payloads are never shown by default, regardless of mode.
        self.include_private_payloads = False

    @property
    def is_status_only(self) -> bool:
        return self.mode == TesterConsoleMode.TESTER_CONSOLE_STATUS_ONLY

    @property
    def is_report_only(self) -> bool:
        return self.mode == TesterConsoleMode.TESTER_CONSOLE_REPORT_ONLY

    @property
    def is_doctor_only(self) -> bool:
        return self.mode == TesterConsoleMode.DOCTOR_ONLY

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id, "purpose": self.purpose,
            "mode": self.mode, "constraints": list(self.constraints),
            "max_runtime_s": self.max_runtime_s,
            "emit_markdown": self.emit_markdown, "emit_html": self.emit_html,
            "include_private_payloads": self.include_private_payloads,
            "read_only": True, "runs_server": False, "opens_browser": False,
            "limitations": list(self.limitations),
        }


def default_console_profile() -> TesterConsoleProfile:
    """The default static console profile (Markdown + optional offline HTML)."""
    return TesterConsoleProfile(
        profile_id=DEFAULT_PROFILE_ID,
        purpose=("a static, local, read-only operator console for the first "
                 "tester release: discover local artifacts and summarize tester "
                 "release status, runs, reports, safety blockers, quarantine, "
                 "membrane status, source diet, bundles, and next actions as "
                 "static Markdown (and optional offline HTML) -- a read-only "
                 "dashboard, not a control panel"),
        mode=TesterConsoleMode.TESTER_CONSOLE_STATIC,
        constraints=list(TesterConsoleConstraint.ALL),
        max_runtime_s=60.0, emit_markdown=True, emit_html=True,
        limitations=[
            "read-only static dashboard; it runs no server and opens no browser",
            "it discovers artifacts read-only and writes only its own console "
            "files; it never modifies run/governance/feeder artifacts",
            "it never starts/controls feeders, controls hardware, accesses the "
            "network/shell/Git/GitHub, or executes artifact contents",
            "raw private event payloads are not displayed by default",
            "it never trains on tester feedback or makes consciousness/life/"
            "agency claims",
            "a green dashboard is operational status, not evidence of inner life"])


def _profile_for_mode(mode: str) -> TesterConsoleProfile:
    p = default_console_profile()
    p.profile_id = f"{mode}_v0"
    p.mode = mode
    p.__post_init__()
    purposes = {
        TesterConsoleMode.TESTER_CONSOLE_MARKDOWN_ONLY:
            "build the static Markdown console only (no HTML)",
        TesterConsoleMode.TESTER_CONSOLE_HTML_STATIC:
            "build the static Markdown + offline HTML console",
        TesterConsoleMode.TESTER_CONSOLE_STATUS_ONLY:
            "compute the console status summary only",
        TesterConsoleMode.TESTER_CONSOLE_REPORT_ONLY:
            "build the console report only",
        TesterConsoleMode.DOCTOR_ONLY:
            "validate console prerequisites only",
    }
    if mode in purposes:
        p.purpose = purposes[mode]
    return p


def get_console_profile(profile_id: Optional[str] = None,
                        ) -> TesterConsoleProfile:
    """Return the named profile, defaulting to ``tester_console_static_v0``."""
    if not profile_id or profile_id == DEFAULT_PROFILE_ID:
        return default_console_profile()
    for mode in TesterConsoleMode.ALL:
        if profile_id in (mode, f"{mode}_v0"):
            return _profile_for_mode(mode)
    p = default_console_profile()
    p.limitations.append(f"requested profile {profile_id!r} unknown; using the "
                         "default static console profile")
    return p


def available_profiles() -> List[str]:
    return [DEFAULT_PROFILE_ID] + [f"{m}_v0" for m in TesterConsoleMode.ALL]
