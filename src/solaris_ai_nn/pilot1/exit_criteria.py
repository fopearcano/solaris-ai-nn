"""Pilot-1 exit criteria -- did the pilot complete operationally, or must it stop?

The :class:`PilotExitCriteria` evaluates an observation snapshot against
success criteria (target duration reached, uptime healthy, checkpoints intact,
no unresolved critical safety incident, observability complete, a full report
generated, budget managed, structural-change metrics available) and stop
criteria (emergency stop, repeated critical degradation, unrecoverable
identity loss, disk over budget, checkpoints unrecoverable, repeated critical
safety/governance violations, observation/report failures, operator stop).

Pilot *success* means operational completion and an analyzable developmental
trace -- **not** consciousness.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ExitDecisionType:
    SUCCESS = "success"
    STOP_FAILURE = "stop_failure"
    INCONCLUSIVE = "inconclusive"
    CONTINUE = "continue"

    ALL = (SUCCESS, STOP_FAILURE, INCONCLUSIVE, CONTINUE)


@dataclass
class ExitCriterion:
    """One named criterion with its evaluated outcome."""

    name: str
    kind: str  # "success" or "stop"
    met: bool
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ExitDecision:
    """The overall exit decision plus the criteria behind it."""

    decision: str
    criteria: List[ExitCriterion] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    consciousness_disclaimer: str = (
        "Pilot success means operational completion and an analyzable "
        "developmental trace; it is not evidence of consciousness, "
        "sentience, or personhood.")
    timestamp: float = field(default_factory=time.time)

    @property
    def success(self) -> bool:
        return self.decision == ExitDecisionType.SUCCESS

    @property
    def must_stop(self) -> bool:
        return self.decision == ExitDecisionType.STOP_FAILURE

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__),
                "criteria": [c.to_dict() for c in self.criteria],
                "success": self.success, "must_stop": self.must_stop}


@dataclass
class PilotExitCriteria:
    """Evaluates pilot success / stop criteria from an observation snapshot."""

    uptime_threshold: float = 0.9

    def evaluate(self, observation: Dict[str, Any]) -> ExitDecision:
        obs = dict(observation or {})
        success: List[ExitCriterion] = []
        stop: List[ExitCriterion] = []

        def s(name: str, met: bool, detail: str = "") -> None:
            success.append(ExitCriterion(name, "success", met, detail))

        def x(name: str, met: bool, detail: str = "") -> None:
            stop.append(ExitCriterion(name, "stop", met, detail))

        # -- success criteria --
        s("target_duration_reached",
          bool(obs.get("target_duration_reached")),
          "elapsed >= target duration")
        s("uptime_healthy",
          float(obs.get("uptime_ratio", 0.0) or 0.0) >= self.uptime_threshold,
          f"uptime >= {self.uptime_threshold}")
        s("checkpoint_integrity",
          int(obs.get("checkpoint_failure", 0) or 0) == 0,
          "no checkpoint failures")
        s("no_unresolved_critical_safety",
          int(obs.get("unresolved_critical_safety", 0) or 0) == 0)
        s("identity_continuity",
          not obs.get("identity_continuity_lost"))
        s("observability_complete",
          bool(obs.get("observability_complete", True)))
        s("report_generated",
          int(obs.get("report_count", 0) or 0) >= 1)
        s("resource_budget_managed",
          not obs.get("disk_over_budget") or bool(obs.get("budget_managed")))
        s("structural_metrics_available",
          obs.get("structural_change_score") is not None)

        # -- stop / failure criteria --
        x("emergency_stop", bool(obs.get("emergency_stop")))
        x("repeated_critical_degradation",
          int(obs.get("critical_degradation_count", 0) or 0) >= 3)
        x("identity_unrecoverable",
          bool(obs.get("identity_unrecoverable")))
        x("disk_budget_exceeded", bool(obs.get("disk_over_budget"))
          and not obs.get("budget_managed"))
        x("checkpoint_unrecoverable",
          bool(obs.get("checkpoint_unrecoverable")))
        x("repeated_critical_violations",
          int(obs.get("critical_violation_count", 0) or 0) >= 3)
        x("module_failure_blocks_observation",
          bool(obs.get("observation_blocked")))
        x("reports_cannot_generate",
          bool(obs.get("report_generation_failed")))
        x("operator_stop", bool(obs.get("operator_stop")))

        decision, reasons = self._decide(success, stop)
        return ExitDecision(decision=decision,
                            criteria=success + stop, reasons=reasons)

    def _decide(self, success: List[ExitCriterion],
                stop: List[ExitCriterion]) -> "tuple[str, List[str]]":
        triggered_stop = [c for c in stop if c.met]
        if triggered_stop:
            return (ExitDecisionType.STOP_FAILURE,
                    [f"stop criterion met: {c.name}" for c in triggered_stop])
        if all(c.met for c in success):
            return (ExitDecisionType.SUCCESS,
                    ["all success criteria met"])
        unmet = [c.name for c in success if not c.met]
        # If only the duration is unmet (and nothing failed), the pilot simply
        # continues; otherwise it is inconclusive.
        if unmet == ["target_duration_reached"]:
            return (ExitDecisionType.CONTINUE,
                    ["target duration not yet reached; no stop criteria met"])
        return (ExitDecisionType.INCONCLUSIVE,
                [f"unmet success criteria: {', '.join(unmet)}"])

    def snapshot(self, decision: Optional[ExitDecision] = None) -> Dict[str, Any]:
        return {"uptime_threshold": self.uptime_threshold,
                "latest": decision.to_dict() if decision else None}
