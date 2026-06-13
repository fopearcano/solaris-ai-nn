"""Habit hygiene -- decay runaway habits, retire dead ones, bounded.

The :class:`HabitHygieneManager` detects dead habits, runaway habits,
context-mismatched habits, poor-outcome loops, and habits that suppress
exploration. It decays/retires within bounds, requests a hypothesis test for
unclear habits, and requests executive stabilization on loops. Safety-related
habits cannot be weakened without governance, and repairs are reversible
where possible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .repair_actions import RepairAction, RepairActionType, make_repair

# Habit labels considered safety-related (weakening needs governance).
SAFETY_HABITS = frozenset({"avoid_danger", "respect_boundary",
                           "safe_shutdown_recommended", "no_action"})


@dataclass
class HabitHygieneManager:
    """Detects habit degradation and proposes bounded, reversible repairs."""

    findings: List[Dict[str, Any]] = field(default_factory=list)
    stabilization_requests: List[str] = field(default_factory=list)

    def detect(self, context: Dict[str, Any]) -> Dict[str, Any]:
        habits = (context or {}).get("habits") or {}
        result = {
            "dead_habits": list(habits.get("dead_habits") or []),
            "runaway_habits": list(habits.get("runaway_habits") or []),
            "context_mismatched": list(habits.get("context_mismatched")
                                       or []),
            "poor_outcome_loops": list(habits.get("poor_outcome_loops")
                                       or []),
            "exploration_suppressing": list(
                habits.get("exploration_suppressing") or []),
        }
        self.findings.append(result)
        self.findings = self.findings[-50:]
        return result

    def propose(self, context: Dict[str, Any]) -> List[RepairAction]:
        detected = self.detect(context)
        actions: List[RepairAction] = []
        for habit in detected["dead_habits"]:
            actions.append(make_repair(
                RepairActionType.RETIRE_DEAD_HABIT, target_ref=str(habit),
                reason="habit no longer reinforced",
                expected_benefit="retire a dead habit"))
        for habit in detected["runaway_habits"]:
            requires_gov = self.is_safety_habit(habit)
            action = make_repair(
                RepairActionType.DECAY_RUNAWAY_HABIT, target_ref=str(habit),
                reason="habit reinforced without bound",
                expected_benefit="decay a runaway habit")
            action.requires_governance = requires_gov
            actions.append(action)
        for habit in detected["poor_outcome_loops"]:
            self.stabilization_requests.append(str(habit))
            actions.append(make_repair(
                RepairActionType.SWITCH_TO_STABILIZATION_MODE,
                target_ref=str(habit),
                reason="habit loop with poor outcomes",
                expected_benefit="request executive stabilization"))
        return actions

    @staticmethod
    def is_safety_habit(label: str) -> bool:
        return str(label).lower() in SAFETY_HABITS

    def snapshot(self) -> Dict[str, Any]:
        return {
            "stabilization_requests": list(self.stabilization_requests),
            "safety_habits": sorted(SAFETY_HABITS),
            "last_finding": self.findings[-1] if self.findings else None,
        }
