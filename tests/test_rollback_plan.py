"""Rollback plan: triggers exist, preserves evidence, no execution."""

from __future__ import annotations

from solaris_ai_nn.experiment_compiler import RollbackTrigger, build_rollback_plan


def test_rollback_triggers_exist():
    plan = build_rollback_plan({"spec_id": "exp_p1"})
    for trigger in ("safety_gate_failure", "test_failure",
                    "claim_guard_failure", "falsification_failure",
                    "operator_rejection"):
        assert trigger in plan.triggers
    assert set(plan.triggers) == set(RollbackTrigger.ALL)


def test_rollback_preserves_evidence():
    plan = build_rollback_plan({"spec_id": "exp_p1"})
    assert plan.to_dict()["preserves_evidence"] is True
    # No step deletes evidence; an explicit step forbids deleting artifacts.
    joined = " ".join(s.instruction for s in plan.steps).lower()
    assert "do not delete" in joined
    assert all(s.preserves_evidence for s in plan.steps)


def test_no_rollback_execution():
    plan = build_rollback_plan({"spec_id": "exp_p1"})
    assert plan.to_dict()["executed"] is False
    md = plan.render_markdown()
    assert "never executed automatically" in md
