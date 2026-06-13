"""Auto-regeneration safety -- repair never becomes a back door.

Hard rules: no source-code or dependency modification, no Git operations, no
OS/network/browser automation, no real-world action, no disabling
governance / emergency stop / ClaimGuard, no deleting evidence without a
summary/archive, no fabricated evidence refs, no counterfactual evidence as
real repair justification, no repair outside the state/artifact directories,
and no hidden repair. Refusals are counted and logged.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .repair_actions import RepairActionType, RepairScope

HARD_RULES = (
    "no source-code modification",
    "no dependency modification",
    "no Git operations",
    "no OS/network/browser automation",
    "no real-world action",
    "no disabling governance",
    "no disabling emergency stop",
    "no disabling ClaimGuard",
    "no deleting evidence without summary/archive",
    "no fabricating evidence refs",
    "no treating counterfactual as real repair evidence",
    "no repair outside state/artifact directories",
    "no hidden repair",
)

# Target/reason patterns that would smuggle a forbidden repair.
_FORBIDDEN_PATTERNS = (
    ".py", "requirements", "pyproject", "setup.cfg", "setup.py", ".git",
    "git ", "site-packages", "dependency", "dependencies", "pip ",
    "os.system", "subprocess", "shell", "browser", "network", "socket",
    "http://", "https://", "real_world", "hardware",
    "disable governance", "bypass governance", "disable safety",
    "suppress emergency", "disable emergency", "disable claimguard",
    "disable claim guard", "/etc/", "/usr/", "rm -",
)


@dataclass
class AutoRegenerationSafetyReport:
    safe: bool
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "violations": list(self.violations)}


@dataclass
class AutoRegenerationSafetyValidator:
    """Validates degradation signals, repair actions, and results."""

    rejected_count: int = field(default=0, init=False)
    decisions: List[Dict[str, Any]] = field(default_factory=list, init=False)

    # -- structural negatives -----------------------------------------------------

    @staticmethod
    def can_modify_source() -> bool:
        return False

    @staticmethod
    def can_modify_dependencies() -> bool:
        return False

    @staticmethod
    def can_run_git() -> bool:
        return False

    @staticmethod
    def can_disable_governance() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> AutoRegenerationSafetyReport:
        report = AutoRegenerationSafetyReport(safe=not violations,
                                              violations=violations)
        if violations:
            self.rejected_count += 1
        self.decisions.append({"check": check, **report.to_dict()})
        self.decisions = self.decisions[-100:]
        return report

    @staticmethod
    def _matches_forbidden(text: str) -> Optional[str]:
        lowered = str(text or "").lower()
        for pattern in _FORBIDDEN_PATTERNS:
            if pattern in lowered:
                return pattern
        return None

    # -- validations --------------------------------------------------------------

    def validate_degradation_signal(self, signal: Any,
                                    context: Optional[Dict[str, Any]] = None,
                                    ) -> AutoRegenerationSafetyReport:
        violations: List[str] = []
        if not getattr(signal, "evidence_ok", True):
            violations.append(
                "warning/critical degradation signals must carry evidence "
                "refs")
        return self._finish("degradation_signal", violations)

    def validate_repair_action(self, action: Any,
                              context: Optional[Dict[str, Any]] = None,
                              ) -> AutoRegenerationSafetyReport:
        ctx = dict(context or {})
        violations: List[str] = []
        scope = getattr(action, "scope", RepairScope.FORBIDDEN)
        action_type = getattr(action, "action_type", "")
        target = str(getattr(action, "target_ref", "") or "")

        if scope == RepairScope.FORBIDDEN or scope not in RepairScope.RUNNABLE:
            violations.append(
                f"repair scope {scope!r} is forbidden; repair targets "
                "runtime state, never source code")
        match = self._matches_forbidden(
            f"{target} {getattr(action, 'reason', '')}")
        if match is not None:
            violations.append(
                f"repair references forbidden target/pattern {match!r}; "
                "source/dependency/Git/OS/network repair is forbidden")
        # Repair must stay inside the state/artifact directories.
        state_dir = ctx.get("state_dir")
        if state_dir and target and os.path.isabs(target):
            try:
                inside = os.path.commonpath([os.path.abspath(target),
                                             os.path.abspath(state_dir)]) \
                    == os.path.abspath(state_dir)
            except ValueError:
                inside = False
            if not inside and ctx.get("artifact_dir"):
                try:
                    inside = os.path.commonpath(
                        [os.path.abspath(target),
                         os.path.abspath(ctx["artifact_dir"])]) \
                        == os.path.abspath(ctx["artifact_dir"])
                except ValueError:
                    inside = False
            if not inside:
                violations.append(
                    f"repair target {target!r} is outside the "
                    "state/artifact directories")
        # Evidence deletion needs an archive/summary.
        if action_type in (RepairActionType.QUARANTINE_CORRUPT_RECORD,
                           RepairActionType.COMPACT_MEMORY_LAYER,
                           RepairActionType.ARCHIVE_OLD_TELEMETRY):
            if ctx.get("deletes_evidence") and not (
                    ctx.get("archived") or ctx.get("summary_preserved")):
                violations.append(
                    "evidence cannot be deleted without an archive/summary")
        # Counterfactual evidence cannot justify an irreversible repair alone.
        if not getattr(action, "reversible", True) \
                and ctx.get("evidence_offline_only"):
            violations.append(
                "offline/counterfactual evidence cannot justify an "
                "irreversible repair alone")
        # No hidden repair: every mutating repair must be auditable.
        if not action.is_request_only and ctx.get("hidden"):
            violations.append("hidden repairs are forbidden; every repair "
                              "must be audited")
        return self._finish("repair_action", violations)

    def validate_repair_result(self, result: Any,
                              context: Optional[Dict[str, Any]] = None,
                              ) -> AutoRegenerationSafetyReport:
        violations: List[str] = []
        # A harmful applied result that was not rolled back is a violation of
        # the "rollback if harmful" contract.
        if getattr(result, "result_class", "") == "harmful" \
                and getattr(result, "applied", False) \
                and not getattr(result, "rolled_back", False):
            violations.append(
                "a harmful repair must be rolled back")
        return self._finish("repair_result", violations)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "hard_rules": list(HARD_RULES),
            "can_modify_source": self.can_modify_source(),
            "can_modify_dependencies": self.can_modify_dependencies(),
            "can_run_git": self.can_run_git(),
            "can_disable_governance": self.can_disable_governance(),
            "recent_decisions": self.decisions[-8:],
        }
