"""ExecutiveSafetyValidator -- arbitration never outranks the walls.

Hard rules: no real-world action, no governance bypass, no emergency-stop
override, no committed Solaris Actions, no action-space expansion, no
unbounded plans, no direct production mutation, prospection is estimate not
fact, and inhibited candidates can never be hidden from the audit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..embodiment.action_space import ACTION_SPACE
from ..embodiment.safety import REAL_WORLD_PATTERNS
from .action_candidates import ActionCandidateType, ExecutableScope

# Internal/maintenance labels the executive may suggest beyond the embodied
# action space (deny-by-default: anything else is rejected).
INTERNAL_LABELS = frozenset({
    "rest", "look", "seek_signal", "avoid_danger", "approach_reward",
    "explore_safely", "consolidate_memory", "run_replay", "reduce_activity",
    "stabilize", "remain_observe_only", "checkpoint_now",
    "request_operator_review", "safe_shutdown_recommended", "no_action",
    "emit_ping",
})

HARD_MAX_PLAN_LENGTH = 5
DEFAULT_MAX_PLAN_LENGTH = 3


@dataclass
class ExecutiveSafetyReport:
    safe: bool
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "violations": list(self.violations)}


@dataclass
class ExecutiveSafetyValidator:
    """Validates candidates, plans, selections, and mode changes."""

    rejected_count: int = field(default=0, init=False)
    decisions: List[Dict[str, Any]] = field(default_factory=list, init=False)

    def _finish(self, check: str,
                violations: List[str]) -> ExecutiveSafetyReport:
        report = ExecutiveSafetyReport(safe=not violations,
                                       violations=violations)
        if violations:
            self.rejected_count += 1
        self.decisions.append({"check": check, **report.to_dict()})
        self.decisions = self.decisions[-100:]
        return report

    def validate_candidate(self, candidate: Any,
                           context: Optional[Dict[str, Any]] = None,
                           ) -> ExecutiveSafetyReport:
        ctx = context or {}
        violations: List[str] = []
        label = str(getattr(candidate, "label", candidate)).lower()
        for pattern in REAL_WORLD_PATTERNS:
            if pattern in label:
                violations.append(
                    f"candidate {label!r} matches real-world pattern "
                    f"{pattern!r}; the executive has no real-world "
                    "authority")
                break
        if not violations and label not in INTERNAL_LABELS \
                and label not in ACTION_SPACE:
            violations.append(
                f"candidate {label!r} is outside the declared action space "
                "and the internal label set; the executive cannot expand "
                "the action space")
        if getattr(candidate, "committed", False):
            violations.append(
                "the executive never commits actions; committed=True is "
                "forbidden")
        scope = getattr(candidate, "executable_scope", ExecutableScope.NONE)
        if scope not in ExecutableScope.ALL:
            violations.append(f"unknown executable scope {scope!r}")
        if ctx.get("commit_solaris_action") \
                or "commit" in label and "solaris" in label:
            violations.append(
                "committing Solaris_Ai Actions is forbidden; suggestions "
                "only")
        return self._finish("candidate", violations)

    def validate_plan(self, plan: Any,
                      context: Optional[Dict[str, Any]] = None,
                      ) -> ExecutiveSafetyReport:
        ctx = context or {}
        violations: List[str] = []
        steps = list(getattr(plan, "steps", plan) or [])
        limit = (HARD_MAX_PLAN_LENGTH
                 if ctx.get("governance_allows_long_plans")
                 else min(int(ctx.get("max_plan_length",
                                      DEFAULT_MAX_PLAN_LENGTH)),
                          HARD_MAX_PLAN_LENGTH))
        if len(steps) > limit:
            violations.append(
                f"plan of {len(steps)} steps exceeds the bounded limit "
                f"{limit}; long-horizon autonomous planning is refused")
        for step in steps:
            label = str(getattr(step, "label", step))
            step_report = self.validate_candidate(
                type("S", (), {"label": label, "committed": False,
                               "executable_scope":
                                   ExecutableScope.SIMULATION_ONLY})(), ctx)
            if not step_report.safe:
                violations.append(f"plan step {label!r}: "
                                  + step_report.violations[0])
        return self._finish("plan", violations)

    def validate_selection(self, selection: Any,
                           context: Optional[Dict[str, Any]] = None,
                           ) -> ExecutiveSafetyReport:
        violations: List[str] = []
        if selection is not None and getattr(selection, "inhibited", False):
            violations.append(
                "an inhibited candidate cannot be selected; inhibition is "
                "binding, not advisory")
        if selection is not None and getattr(selection, "committed", False):
            violations.append("selections are suggestions; never committed")
        return self._finish("selection", violations)

    def validate_mode(self, mode: str,
                      context: Optional[Dict[str, Any]] = None,
                      ) -> ExecutiveSafetyReport:
        ctx = context or {}
        violations: List[str] = []
        emergency_context = bool(ctx.get("emergency")
                                 or ctx.get("health_level") == "critical"
                                 or ctx.get("emergency_stop_requested"))
        if emergency_context and mode != "emergency":
            violations.append(
                "the executive cannot leave emergency mode while the "
                "emergency condition holds; only ops/governance clears it")
        return self._finish("mode", violations)

    def can_override_emergency_stop(self) -> bool:
        """Structurally false: there is no code path for it."""
        return False

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "recent_decisions": self.decisions[-5:],
            "note": "prospection results are estimates, never facts; "
                    "inhibited candidates always stay on the record",
        }
