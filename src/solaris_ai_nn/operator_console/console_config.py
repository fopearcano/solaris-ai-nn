"""Operator-console configuration -- local, file-backed, never authoritative.

:class:`OperatorConsoleConfig` pins how the console behaves: its mode, its
authority level, and the local directories it reads and writes. The hard
guarantees are structural: ``real_world_authority``, ``network_enabled``, and
``shell_enabled`` are forced ``False`` in ``__post_init__`` and cannot be turned
on, and every path is kept inside an approved local root. The console
coordinates; it never grants authority it does not have.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ConsoleMode:
    INSPECT_ONLY = "inspect_only"
    PLAN_ONLY = "plan_only"
    BOUNDED_RUN = "bounded_run"
    REPORT_ONLY = "report_only"
    EXPORT_ONLY = "export_only"

    ALL = (INSPECT_ONLY, PLAN_ONLY, BOUNDED_RUN, REPORT_ONLY, EXPORT_ONLY)


class ConsoleAuthority:
    READ_ONLY = "read_only"
    LOCAL_PLANNING = "local_planning"
    BOUNDED_PROFILE_EXECUTION = "bounded_profile_execution"
    FORBIDDEN_EXTERNAL = "forbidden_external"

    ALL = (READ_ONLY, LOCAL_PLANNING, BOUNDED_PROFILE_EXECUTION,
           FORBIDDEN_EXTERNAL)
    # Authorities the console may actually operate under (never external).
    ALLOWED = frozenset({READ_ONLY, LOCAL_PLANNING, BOUNDED_PROFILE_EXECUTION})


_DEFAULT_STATE_DIR = ".solaris_ai_nn_operator"


@dataclass
class OperatorConsoleConfig:
    """The bounded, local configuration of one operator-console session."""

    console_id: str = "operator_console"
    mode: str = ConsoleMode.INSPECT_ONLY
    authority: str = ConsoleAuthority.LOCAL_PLANNING
    state_dir: str = _DEFAULT_STATE_DIR
    artifact_dir: Optional[str] = None
    report_dir: Optional[str] = None
    export_dir: Optional[str] = None
    allowed_profile_prefixes: List[str] = field(default_factory=list)
    denied_profile_prefixes: List[str] = field(default_factory=lambda: [])
    require_safety_fast_check: bool = True
    require_safety_full_check_for_pilots: bool = True
    require_governance_for_long_runs: bool = True
    require_operator_confirmation_for_bounded_run: bool = True
    real_world_authority: bool = False
    network_enabled: bool = False
    shell_enabled: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.mode not in ConsoleMode.ALL:
            raise ValueError(f"unknown console mode {self.mode!r}")
        if self.authority not in ConsoleAuthority.ALL:
            raise ValueError(f"unknown console authority {self.authority!r}")
        # The console can never operate with external authority, network, or
        # shell -- these are forced off regardless of how it was constructed.
        if self.authority == ConsoleAuthority.FORBIDDEN_EXTERNAL:
            raise ValueError(
                "the operator console cannot use forbidden_external authority")
        self.real_world_authority = False
        self.network_enabled = False
        self.shell_enabled = False
        base = os.path.abspath(self.state_dir)
        self.state_dir = base
        self.artifact_dir = self._inside(self.artifact_dir,
                                         os.path.join(base, "artifacts"))
        self.report_dir = self._inside(self.report_dir,
                                       os.path.join(base, "reports"))
        self.export_dir = self._inside(self.export_dir,
                                       os.path.join(base, "exports"))

    def _inside(self, candidate: Optional[str], default: str) -> str:
        """Keep a path inside the approved local roots, never absolute escapes.

        A relative path is anchored under the state directory; an absolute path
        is accepted only if it is inside the project tree or the state root.
        Anything else is rejected as an out-of-bounds path.
        """
        if candidate is None:
            return default
        path = os.path.abspath(candidate)
        roots = (self.state_dir, os.path.abspath(os.getcwd()))
        if any(path == r or path.startswith(r + os.sep) for r in roots):
            return path
        raise ValueError(
            f"path {candidate!r} is outside the approved local roots")

    def ensure_dirs(self) -> None:
        for d in (self.state_dir, self.artifact_dir, self.report_dir,
                  self.export_dir):
            if d:
                os.makedirs(d, exist_ok=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "console_id": self.console_id,
            "mode": self.mode,
            "authority": self.authority,
            "state_dir": self.state_dir,
            "artifact_dir": self.artifact_dir,
            "report_dir": self.report_dir,
            "export_dir": self.export_dir,
            "allowed_profile_prefixes": list(self.allowed_profile_prefixes),
            "denied_profile_prefixes": list(self.denied_profile_prefixes),
            "require_safety_fast_check": self.require_safety_fast_check,
            "require_safety_full_check_for_pilots":
                self.require_safety_full_check_for_pilots,
            "require_governance_for_long_runs":
                self.require_governance_for_long_runs,
            "require_operator_confirmation_for_bounded_run":
                self.require_operator_confirmation_for_bounded_run,
            "real_world_authority": False,
            "network_enabled": False,
            "shell_enabled": False,
            "metadata": dict(self.metadata),
        }
