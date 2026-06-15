"""InternalActionExecutor: internal-only; external impossible; operator item."""

from __future__ import annotations

from solaris_ai_nn.desire_formation import (
    InternalActionExecutor,
    InternalActionKind,
)


def test_allowed_internal_actions_execute():
    ex = InternalActionExecutor()
    action = ex.execute(InternalActionKind.SHIFT_ATTENTION, "DES_1")
    assert action.completed is True
    assert action.kind == InternalActionKind.SHIFT_ATTENTION
    assert "no hardware/feeder/source" in action.to_dict()["note"]


def test_external_control_impossible():
    ex = InternalActionExecutor()
    # A non-internal (external) action kind is downgraded to a safe no-op.
    action = ex.execute("actuate_robot", "DES_2")
    assert action.kind == InternalActionKind.NO_OP
    assert action.detail["rejected_kind"] == "actuate_robot"


def test_operator_review_creates_decision_item_only():
    ex = InternalActionExecutor()
    action = ex.execute(InternalActionKind.REQUEST_OPERATOR_REVIEW, "DES_3",
                        detail={"reason": "boundary anomaly"})
    assert action.operator_review_item is True
    assert len(ex.operator_review_items) == 1
    assert "no automatic action" in ex.operator_review_items[0]["note"]


def test_no_op_counted():
    ex = InternalActionExecutor()
    ex.execute(InternalActionKind.NO_OP)
    ex.execute(InternalActionKind.NO_OP)
    assert ex.no_op_count == 2
