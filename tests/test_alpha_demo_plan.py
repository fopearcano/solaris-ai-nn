"""Alpha demo plan: steps generated, optional skipped, required blocks, bounded."""

from __future__ import annotations

from solaris_ai_nn.alpha_system import AlphaDemoPlan, AlphaDemoStepStatus


def test_demo_steps_generated():
    plan = AlphaDemoPlan.build()
    assert plan.steps
    ids = {s.step_id for s in plan.steps}
    assert "init_state" in ids
    assert "alpha_report" in ids
    assert "claim_summary" in ids


def test_optional_missing_step_skipped():
    plan = AlphaDemoPlan.build()
    step = plan.get("metabolism_pass")
    step.status = AlphaDemoStepStatus.SKIPPED
    assert step.skipped is True
    assert plan.summary()["alpha_demo_step_skipped_count"] == 1


def test_required_missing_step_blocks():
    plan = AlphaDemoPlan.build()
    step = plan.get("init_state")
    assert step.required is True
    step.status = AlphaDemoStepStatus.BLOCKED
    assert plan.summary()["alpha_demo_step_blocked_count"] == 1


def test_no_step_executes_external():
    plan = AlphaDemoPlan.build()
    assert all(s.to_dict()["executes_external"] is False for s in plan.steps)


def test_foundation_steps_required():
    plan = AlphaDemoPlan.build()
    for sid in ("init_state", "load_fixture", "evidence_summary",
                "alpha_report"):
        assert plan.get(sid).required is True
