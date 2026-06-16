"""Validation plan: stages ordered, safety blocks, no automatic execution."""

from __future__ import annotations

from solaris_ai_nn.experiment_compiler import (
    ValidationStageId,
    build_validation_plan,
)


def test_validation_stages_ordered():
    plan = build_validation_plan({"spec_id": "exp_p1"})
    stage_ids = [s.stage_id for s in plan.stages]
    assert stage_ids == list(ValidationStageId.ORDER)
    assert [s.order for s in plan.stages] == list(
        range(1, len(plan.stages) + 1))


def test_safety_failure_blocks_continuation():
    plan = build_validation_plan({"spec_id": "exp_p1"})
    safety = next(s for s in plan.stages
                  if s.stage_id == ValidationStageId.SAFETY_TESTS)
    assert safety.safety_critical is True
    assert safety.exit_criteria.blocks_continuation_on_failure is True
    # Static inspection precedes unit/integration/safety tests.
    order = [s.stage_id for s in plan.stages]
    assert order.index(ValidationStageId.STATIC_INSPECTION) < order.index(
        ValidationStageId.SAFETY_TESTS)


def test_no_automatic_execution():
    plan = build_validation_plan({"spec_id": "exp_p1"})
    assert plan.to_dict()["auto_executed"] is False
    assert "not\nexecuted automatically" in plan.render_markdown() or \
        "not executed automatically" in plan.render_markdown()


def test_includes_soak_and_replication_followup():
    plan = build_validation_plan({"spec_id": "exp_p1"})
    ids = {s.stage_id for s in plan.stages}
    assert ValidationStageId.MINI_SOAK in ids
    assert ValidationStageId.REPLICATION_REGISTRATION in ids
