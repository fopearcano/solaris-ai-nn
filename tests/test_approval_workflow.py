"""FutureApprovalWorkflow: checklist generated; does not approve action."""

from __future__ import annotations

from solaris_ai_nn.pilot4_planning import FutureApprovalWorkflow


def test_workflow_checklist_generated():
    w = FutureApprovalWorkflow()
    for name in ("preflight_success", "risk_assessment", "consent_record",
                 "safety_case", "operator_approval", "dry_run_replay",
                 "sandbox_replay", "firewall_audit", "emergency_stop_test",
                 "independent_review", "limited_single_action_pilot"):
        assert name in w.step_names(), name


def test_does_not_approve_action():
    w = FutureApprovalWorkflow()
    assert w.is_executable_approval is False
    assert w.can_approve_real_action is False
    result = w.approve()
    assert result["approved"] is False
    assert result["real_world_actuation_enabled"] is False


def test_marking_is_not_approval():
    w = FutureApprovalWorkflow()
    for name in w.step_names():
        w.mark(name, True)
    assert w.completeness == 1.0
    # Even a complete checklist cannot approve a real action.
    assert w.approve()["approved"] is False


def test_snapshot_states_not_executable():
    snap = FutureApprovalWorkflow().snapshot()
    assert snap["is_executable_approval"] is False
    assert snap["can_approve_real_action"] is False
