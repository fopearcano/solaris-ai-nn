"""Console next actions -- recommendations only; the console never executes them.

:class:`NextActionBuilder` derives an ordered list of :class:`ConsoleNextAction`
recommendations from the status model and safety panel. If a safety blocker exists, the
top action is always "fix the blocker" or "stop". Actions are recommendations only; the
console never executes them, and actions requiring manual approval say so.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class NextActionPriority:
    STOP = "stop"
    BLOCKER = "blocker"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

    ALL = (STOP, BLOCKER, HIGH, NORMAL, LOW)
    _RANK = {STOP: 0, BLOCKER: 1, HIGH: 2, NORMAL: 3, LOW: 4}


@dataclass
class ConsoleNextAction:
    """One recommended next action (never executed by the console)."""

    action: str
    priority: str = NextActionPriority.NORMAL
    detail: str = ""
    command: str = ""
    requires_manual_approval: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"action": self.action, "priority": self.priority,
                "detail": self.detail, "command": self.command,
                "requires_manual_approval": self.requires_manual_approval,
                "executed_by_console": False}


@dataclass
class NextActionBuilder:
    """Builds ordered next-action recommendations (read-only)."""

    def build(self, status, safety_panel) -> List[ConsoleNextAction]:
        from .status_model import StageHealth

        actions: List[ConsoleNextAction] = []
        A = ConsoleNextAction
        P = NextActionPriority

        # Safety blockers come first: fix or stop.
        blocking = safety_panel.blocking_findings()
        if blocking:
            actions.append(A(
                "fix safety blocker", P.STOP,
                detail=f"resolve: {blocking[0].detail}",
                requires_manual_approval=True))
            actions.append(A(
                "stop testing until the blocker is resolved", P.STOP,
                detail="do not proceed with a safety blocker open"))

        fixture = status.stage("tester_fixture_demo")
        if fixture and fixture.health in (StageHealth.MISSING_ARTIFACTS,
                                          StageHealth.NOT_STARTED):
            actions.append(A(
                "run the fixture tester demo", P.HIGH,
                detail="the tester release starts with the fixture-only demo",
                command="python -m solaris_ai_nn tester-demo "
                        "--profile fixture_tester_v0"))
        elif fixture and fixture.health == StageHealth.FAILED:
            actions.append(A(
                "fix the fixture demo blocker", P.BLOCKER,
                detail="resolve the fixture reproducibility failure",
                command="inspect the fixture report"))
        else:
            # Fixture present -> recommend live preparation (manual approval).
            live = status.stage("tester_live_init")
            if live and live.health in (StageHealth.NOT_STARTED,
                                        StageHealth.MISSING_ARTIFACTS):
                actions.append(A(
                    "initialize the live tester state", P.NORMAL,
                    detail="prepare governance + feeder templates",
                    command="python -m solaris_ai_nn tester-live-init"))
                actions.append(A(
                    "edit governance manually", P.NORMAL,
                    detail="set live_readonly_enabled + operator_approved",
                    requires_manual_approval=True))
            else:
                actions.append(A(
                    "run the tester live doctor", P.NORMAL,
                    detail="validate live prerequisites before any live run",
                    command="python -m solaris_ai_nn tester-live-doctor"))
                actions.append(A(
                    "proceed to the Prompt 77 feedback ledger / packaging",
                    P.LOW,
                    detail="once fixture + live readiness are green",
                    requires_manual_approval=True))

        # Quarantine inspection if any.
        for f in safety_panel.findings:
            if f.check == "quarantine_present":
                actions.append(A(
                    "inspect the quarantine", P.NORMAL,
                    detail="confirm unsafe events were quarantined, not learned"))
                break

        if not actions:
            actions.append(A("pause", P.LOW,
                             detail="no further action recommended right now"))
        actions.sort(key=lambda a: NextActionPriority._RANK.get(a.priority, 3))
        return actions

    @staticmethod
    def to_dict(actions: List[ConsoleNextAction]) -> Dict[str, Any]:
        return {
            "next_action_count": len(actions),
            "top_action": actions[0].action if actions else "",
            "actions": [a.to_dict() for a in actions],
            "note": "next actions are recommendations only; the console never "
                    "executes them. Actions requiring manual approval say so.",
        }
