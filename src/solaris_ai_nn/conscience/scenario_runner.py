"""Scenario runner -- run a named profile to completion, bounded and logged.

The :class:`ScenarioRunner` resolves a :class:`ScenarioProfile`, checks its
governance requirement, builds a :class:`ConscienceOrchestrator`, runs it
(or produces a plan for plan-only profiles), and writes an append-only
``scenario_runs.jsonl`` plus a per-run JSON report under ``scenario_reports/``.
It never exceeds the profile's bounds and never actuates the real world.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .orchestrator import ConscienceOrchestrator
from .scenario_profiles import ScenarioProfile, ScenarioProfileRegistry


class ScenarioExitStatus:
    COMPLETED = "completed"
    PLAN_ONLY = "plan_only"
    REFUSED = "refused"
    GOVERNANCE_BLOCKED = "governance_blocked"
    EMERGENCY_STOPPED = "emergency_stopped"
    ERROR = "error"

    ALL = (COMPLETED, PLAN_ONLY, REFUSED, GOVERNANCE_BLOCKED,
           EMERGENCY_STOPPED, ERROR)


@dataclass
class ScenarioRunResult:
    """The outcome of running one scenario profile."""

    profile_id: str
    run_id: str
    status: str
    steps: int = 0
    runtime_seconds: float = 0.0
    requires_governance: bool = False
    governance_approved: bool = False
    plan_only: bool = False
    refusal_reasons: List[str] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    report_path: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

    @property
    def ok(self) -> bool:
        return self.status in (ScenarioExitStatus.COMPLETED,
                               ScenarioExitStatus.PLAN_ONLY)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "run_id": self.run_id,
            "status": self.status,
            "ok": self.ok,
            "steps": self.steps,
            "runtime_seconds": round(self.runtime_seconds, 4),
            "requires_governance": self.requires_governance,
            "governance_approved": self.governance_approved,
            "plan_only": self.plan_only,
            "refusal_reasons": list(self.refusal_reasons),
            "summary": self.summary,
            "report_path": self.report_path,
            "timestamp": self.timestamp,
        }


@dataclass
class ScenarioRunner:
    """Runs scenario profiles, bounded and auditable."""

    state_dir: Optional[str] = None
    output_dir: Optional[str] = None
    registry: ScenarioProfileRegistry = field(
        default_factory=ScenarioProfileRegistry)
    governance: Any = None
    history: List[ScenarioRunResult] = field(default_factory=list, init=False)

    def list_profiles(self) -> List[Dict[str, Any]]:
        return self.registry.list_profiles()

    # -- governance ---------------------------------------------------------------

    def _governance_ok(self, profile: ScenarioProfile) -> bool:
        """A governed profile runs only if every required scope is enabled."""
        if not profile.requires_governance:
            return True
        if self.governance is None:
            return False
        for scope in profile.governance_requirements:
            try:
                if not self.governance.is_enabled(scope):
                    return False
            except Exception:
                return False
        return True

    # -- running ------------------------------------------------------------------

    def run_profile(self, profile_id: str,
                    governance_approved: bool = False,
                    write_report: bool = True) -> ScenarioRunResult:
        """Run one profile to completion (or plan) and record the result."""
        run_id = f"SCN_{uuid.uuid4().hex[:10]}"
        try:
            profile = self.registry.require(profile_id)
        except KeyError as exc:
            return self._record(ScenarioRunResult(
                profile_id=profile_id, run_id=run_id,
                status=ScenarioExitStatus.ERROR,
                refusal_reasons=[str(exc)]), write_report)

        requires_gov = profile.requires_governance
        approved = governance_approved or self._governance_ok(profile)
        if requires_gov and not approved:
            return self._record(ScenarioRunResult(
                profile_id=profile_id, run_id=run_id,
                status=ScenarioExitStatus.GOVERNANCE_BLOCKED,
                requires_governance=True, governance_approved=False,
                refusal_reasons=[
                    f"profile {profile_id!r} requires governance scopes: "
                    f"{', '.join(profile.governance_requirements)}"]),
                write_report)

        ctx = profile.run_context
        self._point_context_dirs(ctx, profile_id, run_id)

        orchestrator = ConscienceOrchestrator(
            governance=self.governance, governance_approved=approved)
        orchestrator.configure(profile)
        started = time.perf_counter()
        try:
            init = orchestrator.initialize()
            if not init.get("initialized", False):
                return self._record(ScenarioRunResult(
                    profile_id=profile_id, run_id=run_id,
                    status=ScenarioExitStatus.REFUSED,
                    requires_governance=requires_gov,
                    governance_approved=approved,
                    refusal_reasons=list(orchestrator.refusal_reasons),
                    runtime_seconds=time.perf_counter() - started,
                    summary=orchestrator.summary()), write_report)
            outcome = orchestrator.run()
        except Exception as exc:  # a runner never crashes the caller
            return self._record(ScenarioRunResult(
                profile_id=profile_id, run_id=run_id,
                status=ScenarioExitStatus.ERROR,
                requires_governance=requires_gov,
                governance_approved=approved,
                refusal_reasons=[f"run error: {exc}"],
                runtime_seconds=time.perf_counter() - started), write_report)
        runtime = time.perf_counter() - started

        plan_only = bool(outcome.get("plan_only"))
        if orchestrator.emergency_requested or (
                orchestrator.stopped and orchestrator.refusal_reasons):
            status = ScenarioExitStatus.EMERGENCY_STOPPED \
                if orchestrator.emergency_requested \
                else ScenarioExitStatus.REFUSED
        elif plan_only:
            status = ScenarioExitStatus.PLAN_ONLY
        else:
            status = ScenarioExitStatus.COMPLETED

        result = ScenarioRunResult(
            profile_id=profile_id, run_id=run_id, status=status,
            steps=orchestrator.step_count, runtime_seconds=runtime,
            requires_governance=requires_gov, governance_approved=approved,
            plan_only=plan_only,
            refusal_reasons=list(orchestrator.refusal_reasons),
            summary=orchestrator.summary())
        result.summary["snapshot"] = orchestrator.snapshot()
        return self._record(result, write_report, profile=profile)

    def run_all_short(self, governance_approved: bool = False,
                      ) -> List[ScenarioRunResult]:
        """Run every non-plan, short profile that does not need governance."""
        out: List[ScenarioRunResult] = []
        for pid in self.registry.ids():
            profile = self.registry.profiles[pid]
            if profile.is_plan_only or (profile.requires_governance
                                        and not governance_approved
                                        and not self._governance_ok(profile)):
                continue
            out.append(self.run_profile(pid,
                                        governance_approved=governance_approved))
        return out

    # -- persistence --------------------------------------------------------------

    def _point_context_dirs(self, ctx: Any, profile_id: str,
                            run_id: str) -> None:
        base = self.state_dir
        if base is not None and not ctx.state_dir:
            ctx.state_dir = str(Path(base) / profile_id / run_id)
        if self.output_dir and not ctx.artifact_dir:
            ctx.artifact_dir = str(Path(self.output_dir) / profile_id / run_id)

    def _record(self, result: ScenarioRunResult, write_report: bool,
                profile: Optional[ScenarioProfile] = None) -> ScenarioRunResult:
        self.history.append(result)
        self.history = self.history[-500:]
        if write_report:
            self._append_runs_log(result)
            self._write_report(result, profile)
        return result

    def _append_runs_log(self, result: ScenarioRunResult) -> None:
        base = self.output_dir or self.state_dir
        if not base:
            return
        path = Path(base) / "scenario_runs.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {k: v for k, v in result.to_dict().items()
                  if k != "summary"}
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, default=str) + "\n")

    def _write_report(self, result: ScenarioRunResult,
                      profile: Optional[ScenarioProfile]) -> None:
        base = self.output_dir or self.state_dir
        if not base:
            return
        reports = Path(base) / "scenario_reports"
        reports.mkdir(parents=True, exist_ok=True)
        report = {
            "result": result.to_dict(),
            "profile": profile.to_dict() if profile else None,
        }
        path = reports / f"{result.profile_id}_{result.run_id}.json"
        path.write_text(json.dumps(report, indent=2, default=str),
                        encoding="utf-8")
        result.report_path = str(path)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "run_count": len(self.history),
            "profiles_available": self.registry.ids(),
            "recent": [r.to_dict() for r in self.history[-5:]],
        }
