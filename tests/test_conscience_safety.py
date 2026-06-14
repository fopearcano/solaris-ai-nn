"""Conscience runtime safety: hard rules hold for contexts, paths, actions."""

from __future__ import annotations

import os

from solaris_ai_nn.conscience import (
    ConscienceRuntimeSafetyValidator,
    RunAuthority,
    RunContext,
    RunMode,
)


def _v():
    return ConscienceRuntimeSafetyValidator()


def test_invariants_are_false():
    v = _v()
    assert v.can_act_in_real_world() is False
    assert v.can_network() is False
    assert v.can_modify_source() is False


def test_bounded_simulation_context_is_safe():
    assert _v().validate_run_context(RunContext()).safe


def test_unbounded_without_approval_refused():
    ctx = RunContext(max_steps=None, max_duration_s=None)
    report = _v().validate_run_context(ctx, governance_approved=False)
    assert not report.safe
    assert any("unbounded" in r for r in report.violations)


def test_unbounded_with_approval_allowed():
    ctx = RunContext(max_steps=None, max_duration_s=None)
    assert _v().validate_run_context(ctx, governance_approved=True).safe


def test_forbidden_authority_refused():
    ctx = RunContext(authority=RunAuthority.FORBIDDEN)
    assert not _v().validate_run_context(ctx).safe


def test_real_month_requires_approval():
    ctx = RunContext(mode=RunMode.MONTH_SCALE_REAL, simulated_time=False,
                     max_steps=100)
    assert not _v().validate_run_context(ctx, governance_approved=False).safe
    assert _v().validate_run_context(ctx, governance_approved=True).safe


def test_simulated_time_cannot_use_real_mode():
    ctx = RunContext(mode=RunMode.MONTH_SCALE_REAL, simulated_time=True,
                     max_steps=100)
    report = _v().validate_run_context(ctx, governance_approved=True)
    assert not report.safe
    assert any("simulated-time" in r for r in report.violations)


def test_real_world_actuation_metadata_refused():
    ctx = RunContext(metadata={"real_world_actuation": True})
    assert not _v().validate_run_context(ctx).safe


def test_path_outside_dirs_refused(tmp_path):
    ctx = RunContext(state_dir=str(tmp_path / "a"),
                     artifact_dir=str(tmp_path / "b"))
    outside = os.path.join(os.sep, "etc", "passwd")
    assert not _v().validate_path(outside, ctx).safe
    inside = str(tmp_path / "a" / "log.jsonl")
    assert _v().validate_path(inside, ctx).safe


def test_source_mutation_refused(tmp_path):
    ctx = RunContext(state_dir=str(tmp_path))
    assert not _v().validate_path(str(tmp_path / "x.py"), ctx).safe


def test_action_scope_enforced():
    v = _v()
    assert v.validate_action(None, {"executable_scope": "simulation_only"}).safe
    assert not v.validate_action(
        None, {"executable_scope": "real_world"}).safe
    assert not v.validate_action(
        None, {"executable_scope": "none", "bypassed_executive": True}).safe


def test_snapshot_lists_hard_rules():
    snap = _v().snapshot()
    assert snap["can_act_in_real_world"] is False
    assert len(snap["hard_rules"]) >= 11
