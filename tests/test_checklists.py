"""Tests for the governance checklists."""

from __future__ import annotations

from solaris_ai_nn.governance.checklists import (
    ALL_CHECKLISTS,
    long_soak_checklist,
    plasticity_checklist,
    post_run_checklist,
    pre_run_checklist,
    sidecar_checklist,
)


def _all_true(checklist):
    return {item_id: True for item_id in checklist.item_ids()}


def test_pre_run_checklist_passes_with_valid_config():
    checklist = pre_run_checklist()
    result = checklist.evaluate(_all_true(checklist))
    assert result.passed
    assert not result.failed_required
    assert len(result.items) == 9


def test_pre_run_checklist_fails_without_bounds():
    checklist = pre_run_checklist()
    ctx = _all_true(checklist)
    ctx["bounds_set"] = False
    result = checklist.evaluate(ctx)
    assert not result.passed
    assert "bounds_set" in result.failed_required


def test_long_soak_checklist_fails_if_restart_test_missing():
    checklist = long_soak_checklist()
    ctx = _all_true(checklist)
    ctx["restart_test_passed"] = False
    result = checklist.evaluate(ctx)
    assert not result.passed
    assert "restart_test_passed" in result.failed_required


def test_post_run_checklist_requires_final_checkpoint():
    checklist = post_run_checklist()
    ctx = _all_true(checklist)
    ctx["final_checkpoint_exists"] = False
    result = checklist.evaluate(ctx)
    assert not result.passed
    assert "final_checkpoint_exists" in result.failed_required


def test_post_run_advisory_items_do_not_fail():
    checklist = post_run_checklist()
    ctx = _all_true(checklist)
    ctx["benchmark_report_generated"] = False  # advisory
    ctx["language_report_saved_if_enabled"] = False  # advisory
    result = checklist.evaluate(ctx)
    assert result.passed


def test_plasticity_checklist_items():
    checklist = plasticity_checklist()
    assert set(checklist.item_ids()) == {
        "dry_run_completed", "rollback_tested", "audit_enabled",
        "safety_validator_active", "mutation_bounds_reviewed"}


def test_sidecar_checklist_items():
    checklist = sidecar_checklist()
    assert "no_action_authority" in checklist.item_ids()
    assert "detach_tested" in checklist.item_ids()


def test_missing_context_keys_fail_required_items():
    result = pre_run_checklist().evaluate({})
    assert not result.passed
    assert len(result.failed_required) == 9


def test_result_serializes_and_renders():
    checklist = pre_run_checklist()
    result = checklist.evaluate(_all_true(checklist))
    data = result.to_dict()
    assert data["name"] == "pre_run" and data["passed"]
    md = result.to_markdown()
    assert "- [x]" in md and "PASSED" in md
    assert set(ALL_CHECKLISTS) == {"pre_run", "long_soak", "plasticity",
                                   "sidecar", "post_run"}
