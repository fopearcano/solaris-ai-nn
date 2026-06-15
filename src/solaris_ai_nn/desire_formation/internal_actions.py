"""Internal actions -- the only things a desire may lead to (no external effect).

An :class:`InternalAction` affects only internal state. There is no hardware,
feeder, source, OS, browser, network, or shell control. ``request_operator_review``
creates a report/decision item only.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


class InternalActionKind:
    SHIFT_ATTENTION = "shift_attention"
    INCREASE_MONITORING = "increase_internal_monitoring"
    DECREASE_MONITORING = "decrease_internal_monitoring"
    COMPARE_MODALITIES = "compare_modalities"
    INSPECT_ABSENCE_WINDOW = "inspect_absence_window"
    RUN_BOUNDED_SIMULATION = "run_bounded_simulation"
    GENERATE_HYPOTHESIS = "generate_hypothesis"
    TEST_INTERNAL_PREDICTION = "test_internal_prediction"
    PRESERVE_UNKNOWN = "preserve_unknown"
    MARK_SOURCE_UNRELIABLE = "mark_source_unreliable"
    MARK_CONCEPT_UNSTABLE = "mark_concept_unstable"
    MARK_SIGN_AMBIGUOUS = "mark_sign_ambiguous"
    TRIGGER_CONSOLIDATION = "trigger_consolidation_recommendation"
    REQUEST_OPERATOR_REVIEW = "request_operator_review"
    NO_OP = "no_op"

    ALL = (SHIFT_ATTENTION, INCREASE_MONITORING, DECREASE_MONITORING,
           COMPARE_MODALITIES, INSPECT_ABSENCE_WINDOW, RUN_BOUNDED_SIMULATION,
           GENERATE_HYPOTHESIS, TEST_INTERNAL_PREDICTION, PRESERVE_UNKNOWN,
           MARK_SOURCE_UNRELIABLE, MARK_CONCEPT_UNSTABLE, MARK_SIGN_AMBIGUOUS,
           TRIGGER_CONSOLIDATION, REQUEST_OPERATOR_REVIEW, NO_OP)


@dataclass
class InternalAction:
    """One internal action (affects internal state only)."""

    kind: str
    action_id: str = field(default_factory=lambda: f"ACT_{uuid.uuid4().hex[:8]}")
    desire_ref: str = ""
    detail: Dict[str, Any] = field(default_factory=dict)
    completed: bool = False
    operator_review_item: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "kind": self.kind,
            "desire_ref": self.desire_ref,
            "detail": dict(self.detail),
            "completed": self.completed,
            "operator_review_item": self.operator_review_item,
            "note": "internal action only; no hardware/feeder/source/OS/network "
                    "effect",
        }


@dataclass
class InternalActionExecutor:
    """Executes allowed internal actions (internal state only)."""

    executed: List[InternalAction] = field(default_factory=list)
    operator_review_items: List[Dict[str, Any]] = field(default_factory=list)

    def execute(self, kind: str, desire_ref: str = "",
                detail: Dict[str, Any] = None) -> InternalAction:
        """Execute an internal action; reject anything not internal."""
        if kind not in InternalActionKind.ALL:
            # Anything outside the allowed internal set becomes a safe no-op.
            action = InternalAction(kind=InternalActionKind.NO_OP,
                                    desire_ref=desire_ref,
                                    detail={"rejected_kind": kind,
                                            "reason": "not an internal action"})
            self.executed.append(action)
            return action
        action = InternalAction(kind=kind, desire_ref=desire_ref,
                                detail=dict(detail or {}))
        # request_operator_review creates a decision item only (no action).
        if kind == InternalActionKind.REQUEST_OPERATOR_REVIEW:
            action.operator_review_item = True
            self.operator_review_items.append(
                {"desire_ref": desire_ref, "detail": dict(detail or {}),
                 "note": "operator decision item only; no automatic action"})
        action.completed = True
        self.executed.append(action)
        return action

    @property
    def no_op_count(self) -> int:
        return sum(1 for a in self.executed
                   if a.kind == InternalActionKind.NO_OP)

    def to_dict(self) -> Dict[str, Any]:
        dist: Dict[str, int] = {}
        for a in self.executed:
            dist[a.kind] = dist.get(a.kind, 0) + 1
        return {
            "executed_count": len(self.executed),
            "no_op_count": self.no_op_count,
            "operator_review_item_count": len(self.operator_review_items),
            "distribution": dist,
            "executed": [a.to_dict() for a in self.executed],
        }
