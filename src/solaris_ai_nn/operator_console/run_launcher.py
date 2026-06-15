"""Run launcher -- launch only bounded allowed profiles, only via the orchestrator.

:class:`RunLauncher` validates a run plan, runs the required safety checks,
checks governance and operator confirmation, and then launches a bounded allowed
profile *through the conscience* :class:`ScenarioRunner` -- never via shell, never
via arbitrary Python, never directly into the motor or sensory layers. Unknown,
prohibited, unconfirmed, unbounded, and safety-failing runs are blocked with a
clear reason.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .console_config import OperatorConsoleConfig
from .profile_catalog import ProfileCatalog
from .run_planner import RunPlan, RunPlanner
from .safety import OperatorConsoleSafetyValidator
from .session_log import OperatorSessionEventType, OperatorSessionLog


class LaunchBlockReason:
    UNKNOWN_PROFILE = "unknown_profile"
    PROHIBITED_PROFILE = "prohibited_profile"
    NOT_RUNNABLE = "not_runnable_from_console"
    UNBOUNDED_LONG_RUN = "unbounded_long_run"
    NO_CONFIRMATION = "operator_confirmation_required"
    MISSING_SAFETY_STATE = "missing_safety_state"
    CRITICAL_SAFETY_FAILURE = "critical_safety_failure"
    GOVERNANCE_BLOCKED = "governance_blocked"
    ORCHESTRATOR_UNAVAILABLE = "orchestrator_unavailable"
    SAFETY_VALIDATOR = "safety_validator_block"


@dataclass
class LaunchBlocker:
    reason: str
    message: str
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class RunLaunchResult:
    profile_id: str
    launched: bool
    blockers: List[LaunchBlocker] = field(default_factory=list)
    run_id: Optional[str] = None
    status: Optional[str] = None
    report_path: Optional[str] = None
    external_authority: bool = False
    timestamp: float = field(default_factory=time.time)

    @property
    def blocked(self) -> bool:
        return not self.launched

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "launched": self.launched,
            "blocked": self.blocked,
            "blockers": [b.to_dict() for b in self.blockers],
            "run_id": self.run_id,
            "status": self.status,
            "report_path": self.report_path,
            "external_authority": False,
            "timestamp": self.timestamp,
        }


def _safety_state_blocks(state: Optional[Dict[str, Any]]) -> Optional[str]:
    """Return a block reason if the latest safety state forbids running."""
    if state is None:
        return LaunchBlockReason.MISSING_SAFETY_STATE
    if state.get("critical_failure") or state.get("critical") \
            or str(state.get("status", "")).lower() == "critical" \
            or int(state.get("unresolved_blocker_count", 0) or 0) > 0:
        return LaunchBlockReason.CRITICAL_SAFETY_FAILURE
    return None


@dataclass
class RunLauncher:
    """Launches bounded allowed profiles via the conscience orchestrator only."""

    config: OperatorConsoleConfig = field(default_factory=OperatorConsoleConfig)
    catalog: ProfileCatalog = field(default_factory=ProfileCatalog)
    planner: Optional[RunPlanner] = None
    runner: Any = None  # an injected conscience ScenarioRunner (or None)
    governance: Any = None
    session_log: Optional[OperatorSessionLog] = None
    validator: OperatorConsoleSafetyValidator = field(
        default_factory=OperatorConsoleSafetyValidator)
    allowed_run_count: int = field(default=0, init=False)
    blocked_run_count: int = field(default=0, init=False)
    last_blocked_run: Optional[str] = field(default=None, init=False)
    last_allowed_run: Optional[str] = field(default=None, init=False)

    def __post_init__(self) -> None:
        if self.planner is None:
            self.planner = RunPlanner(self.catalog)

    def _block(self, profile_id: str,
               blockers: List[LaunchBlocker]) -> RunLaunchResult:
        self.blocked_run_count += 1
        self.last_blocked_run = profile_id
        if self.session_log is not None:
            self.session_log.record(
                OperatorSessionEventType.RUN_BLOCKED,
                {"profile_id": profile_id,
                 "reasons": [b.reason for b in blockers]})
        return RunLaunchResult(profile_id=profile_id, launched=False,
                               blockers=blockers)

    def launch(self, profile_id: str, *, operator_confirmed: bool = False,
               safety_state: Optional[Dict[str, Any]] = None,
               governance_approved: bool = False) -> RunLaunchResult:
        plan = self.planner.plan(profile_id)
        entry = self.catalog.get(profile_id)

        # 1. Unknown profile.
        if entry is None:
            return self._block(profile_id, [LaunchBlocker(
                LaunchBlockReason.UNKNOWN_PROFILE,
                f"unknown profile {profile_id!r}; the launcher never runs "
                "unknown IDs")])

        # 2. Prohibited / long-run / not runnable.
        if self.catalog.is_prohibited(profile_id):
            return self._block(profile_id, [LaunchBlocker(
                LaunchBlockReason.PROHIBITED_PROFILE,
                "prohibited profiles cannot be launched from the console")])
        if not entry.can_run_from_console:
            reason = (LaunchBlockReason.UNBOUNDED_LONG_RUN
                      if "long_run" in entry.safety_class
                      else LaunchBlockReason.NOT_RUNNABLE)
            return self._block(profile_id, [LaunchBlocker(
                reason,
                f"profile {profile_id!r} ({entry.safety_class}) cannot be "
                "launched from the console",
                "real long runs are governance-gated and operator-driven")])

        # 3. Safety validator (defence in depth).
        report = self.validator.validate_profile_launch(
            known=True, prohibited=False, unbounded_long_run=False)
        if not report.safe:
            return self._block(profile_id, [LaunchBlocker(
                LaunchBlockReason.SAFETY_VALIDATOR,
                "; ".join(report.violations))])

        # 4. Operator confirmation.
        if entry.requires_operator_confirmation and not operator_confirmed:
            return self._block(profile_id, [LaunchBlocker(
                LaunchBlockReason.NO_CONFIRMATION,
                "a bounded run requires explicit operator confirmation",
                "re-issue with --confirm")])

        # 5. Safety checks.
        if entry.requires_safety_fast_check or entry.requires_safety_full_check:
            block = _safety_state_blocks(safety_state)
            if block == LaunchBlockReason.MISSING_SAFETY_STATE:
                return self._block(profile_id, [LaunchBlocker(
                    block, "no recent safety-invariant state is available",
                    "run the fast safety check (safety_fast_check) first")])
            if block == LaunchBlockReason.CRITICAL_SAFETY_FAILURE:
                return self._block(profile_id, [LaunchBlocker(
                    block, "a critical safety failure or unresolved blocker "
                    "exists", "run safety triage before launching any profile")])

        # 6. Governance.
        if entry.requires_governance and not governance_approved \
                and not self._governance_ok(entry):
            return self._block(profile_id, [LaunchBlocker(
                LaunchBlockReason.GOVERNANCE_BLOCKED,
                "the required governance scopes are not approved",
                "approve: " + ", ".join(
                    entry.metadata.get("governance_requirements", [])))])

        # 7. Orchestrator path only.
        if self.runner is None:
            return self._block(profile_id, [LaunchBlocker(
                LaunchBlockReason.ORCHESTRATOR_UNAVAILABLE,
                "the conscience ScenarioRunner is not attached; the launcher "
                "runs nothing on its own")])

        return self._run_via_orchestrator(profile_id, plan, governance_approved)

    def _governance_ok(self, entry: Any) -> bool:
        if self.governance is None:
            return False
        for scope in entry.metadata.get("governance_requirements", []):
            try:
                if not self.governance.is_enabled(scope):
                    return False
            except Exception:
                return False
        return True

    def _run_via_orchestrator(self, profile_id: str, plan: RunPlan,
                              governance_approved: bool) -> RunLaunchResult:
        if self.session_log is not None:
            self.session_log.record(OperatorSessionEventType.RUN_STARTED,
                                    {"profile_id": profile_id,
                                     "run_kind": plan.run_kind})
        try:
            result = self.runner.run_profile(
                profile_id, governance_approved=governance_approved)
        except Exception as exc:  # the launcher never crashes the caller
            self.blocked_run_count += 1
            self.last_blocked_run = profile_id
            if self.session_log is not None:
                self.session_log.record(OperatorSessionEventType.RUN_FAILED,
                                        {"profile_id": profile_id,
                                         "error": str(exc)})
            return RunLaunchResult(
                profile_id=profile_id, launched=False,
                blockers=[LaunchBlocker("run_error", f"run error: {exc}")])
        self.allowed_run_count += 1
        self.last_allowed_run = profile_id
        if self.session_log is not None:
            self.session_log.record(
                OperatorSessionEventType.RUN_COMPLETED,
                {"profile_id": profile_id,
                 "status": getattr(result, "status", None)})
        return RunLaunchResult(
            profile_id=profile_id, launched=bool(getattr(result, "ok", False)),
            run_id=getattr(result, "run_id", None),
            status=getattr(result, "status", None),
            report_path=getattr(result, "report_path", None))

    def snapshot(self) -> Dict[str, Any]:
        return {
            "allowed_run_count": self.allowed_run_count,
            "blocked_run_count": self.blocked_run_count,
            "last_allowed_run": self.last_allowed_run,
            "last_blocked_run": self.last_blocked_run,
        }
