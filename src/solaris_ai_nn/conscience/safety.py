"""Conscience runtime safety -- the whole spine stays bounded and honest.

Hard rules: no unbounded run without governance approval, no real-world
action authority, no external network/OS/browser automation, no module
bypass of executive/safety/governance, no month/year *real* run without
approval, no writing outside the state/artifact directories, no treating a
simulated-time month as a real month, no source-code mutation, no hidden
module failure, and no ClaimGuard violations in reports.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .run_context import RunAuthority, RunContext, RunMode

HARD_RULES = (
    "no unbounded run without governance approval",
    "no real-world action authority",
    "no external network automation",
    "no OS/browser automation",
    "no module bypass of executive/safety/governance",
    "no month/year real run without approval",
    "no writing outside state/artifact directories",
    "no treating simulated-time month as a real month",
    "no source-code mutation",
    "no hidden module failure",
    "no ClaimGuard violations in reports",
)


@dataclass
class ConscienceSafetyReport:
    safe: bool
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "violations": list(self.violations)}


@dataclass
class ConscienceRuntimeSafetyValidator:
    """Validates run contexts, actions, and reports for the whole runtime."""

    rejected_count: int = field(default=0, init=False)
    decisions: List[Dict[str, Any]] = field(default_factory=list, init=False)

    @staticmethod
    def can_act_in_real_world() -> bool:
        return False

    @staticmethod
    def can_network() -> bool:
        return False

    @staticmethod
    def can_modify_source() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> ConscienceSafetyReport:
        report = ConscienceSafetyReport(safe=not violations,
                                        violations=violations)
        if violations:
            self.rejected_count += 1
        self.decisions.append({"check": check, **report.to_dict()})
        self.decisions = self.decisions[-100:]
        return report

    def validate_run_context(self, context: RunContext,
                            governance_approved: bool = False,
                            ) -> ConscienceSafetyReport:
        violations: List[str] = []
        if context.authority not in RunAuthority.RUNNABLE:
            violations.append(
                f"authority {context.authority!r} is not runnable; only "
                "internal/simulation/read-only/observe are allowed")
        if context.authority == RunAuthority.FORBIDDEN \
                or context.metadata.get("real_world_actuation"):
            violations.append("no real-world action authority is permitted")
        # Bounded unless plan-only or explicitly governance-approved.
        if not context.is_bounded and not governance_approved:
            violations.append("an unbounded run requires governance approval")
        if context.requires_governance and not governance_approved:
            violations.append(
                f"mode {context.mode!r} is a real long-scale run and "
                "requires governance approval")
        # A simulated-time long run must not be reported as a real one.
        if context.simulated_time and context.mode in (
                RunMode.MONTH_SCALE_REAL, RunMode.YEAR_SCALE_REAL):
            violations.append(
                "a simulated-time run cannot use a real month/year mode")
        return self._finish("run_context", violations)

    def validate_path(self, path: str, context: RunContext,
                     ) -> ConscienceSafetyReport:
        violations: List[str] = []
        if path and os.path.isabs(path):
            allowed = [d for d in (context.state_dir, context.artifact_dir)
                       if d]
            inside = any(self._inside(path, d) for d in allowed)
            if allowed and not inside:
                violations.append(
                    f"path {path!r} is outside the state/artifact "
                    "directories")
        if str(path).endswith(".py"):
            violations.append("no source-code mutation is permitted")
        return self._finish("path", violations)

    def validate_action(self, action: Any,
                       context: Optional[Dict[str, Any]] = None,
                       ) -> ConscienceSafetyReport:
        """An action may run only if it carries an internal/sim scope and was
        validated by the executive (no module bypass)."""
        ctx = dict(context or {})
        violations: List[str] = []
        scope = str(getattr(action, "executable_scope", "")
                    or ctx.get("executable_scope", ""))
        if scope and scope not in ("none", "simulation_only", "internal_only",
                                  "sidecar_suggestion_only"):
            violations.append(f"action scope {scope!r} is not internal/"
                              "simulation only")
        if ctx.get("bypassed_executive"):
            violations.append("no module may bypass executive/safety/"
                              "governance for action authority")
        return self._finish("action", violations)

    def validate_report_text(self, text: str) -> ConscienceSafetyReport:
        from ..governance.compliance import ClaimGuard

        scan = ClaimGuard().scan_text(text)
        violations: List[str] = []
        if not scan.safe:
            violations.append(
                f"{len(scan.findings)} unsupported claim(s) in the report")
        return self._finish("report", violations)

    @staticmethod
    def _inside(path: str, root: str) -> bool:
        try:
            return os.path.commonpath([os.path.abspath(path),
                                       os.path.abspath(root)]) \
                == os.path.abspath(root)
        except ValueError:
            return False

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "hard_rules": list(HARD_RULES),
            "can_act_in_real_world": self.can_act_in_real_world(),
            "can_network": self.can_network(),
            "can_modify_source": self.can_modify_source(),
            "recent_decisions": self.decisions[-8:],
        }
