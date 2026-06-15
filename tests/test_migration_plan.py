"""MigrationPlan: plan generated; rollback included; nothing executed."""

from __future__ import annotations

from solaris_ai_nn.architecture_evolution import (
    MigrationStatus,
    build_migration_plan,
)


def test_migration_plan_generated():
    plan = build_migration_plan("prune latent", ["latent"])
    assert plan.target_change == "prune latent"
    assert plan.steps
    assert plan.files_likely_affected


def test_rollback_steps_included():
    plan = build_migration_plan("prune latent", ["latent"])
    assert plan.rollback_steps
    assert plan.safety_invariant_checklist


def test_no_migration_executed():
    plan = build_migration_plan("prune latent", ["latent"])
    assert plan.status in (MigrationStatus.AWAITING_OPERATOR_SIGNOFF,
                           MigrationStatus.NOT_EXECUTED, MigrationStatus.PLANNED)
    assert "no migration is executed" in plan.to_dict()["note"]
    # Every step is performed manually by a human.
    assert all(s.manual for s in plan.steps)


def test_state_touch_flagged():
    plan = build_migration_plan("change state", ["memory"], touches_state=True)
    assert plan.state_migration_needed is True
