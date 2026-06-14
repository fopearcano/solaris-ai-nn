"""Conscience run context: modes, authorities, bounds, governance gating."""

from __future__ import annotations

import pytest

from solaris_ai_nn.conscience import RunAuthority, RunBoundary, RunContext, RunMode


def test_defaults_are_bounded_and_simulation_only():
    ctx = RunContext()
    assert ctx.authority == RunAuthority.SIMULATION_ONLY
    assert ctx.is_bounded
    assert not ctx.requires_governance
    assert not ctx.is_plan_only


def test_unknown_mode_and_authority_rejected():
    with pytest.raises(ValueError):
        RunContext(mode="not_a_mode")
    with pytest.raises(ValueError):
        RunContext(authority="not_an_authority")


def test_real_long_scale_requires_governance():
    ctx = RunContext(mode=RunMode.MONTH_SCALE_REAL)
    assert ctx.requires_governance
    ctx2 = RunContext(mode=RunMode.YEAR_SCALE_REAL)
    assert ctx2.requires_governance


def test_plan_only_modes():
    assert RunContext(mode=RunMode.MONTH_SCALE_PLAN).is_plan_only
    assert RunContext(mode=RunMode.YEAR_SCALE_PLAN).is_plan_only


def test_forbidden_not_runnable():
    assert RunAuthority.FORBIDDEN not in RunAuthority.RUNNABLE
    for a in (RunAuthority.INTERNAL_ONLY, RunAuthority.SIMULATION_ONLY,
              RunAuthority.READ_ONLY, RunAuthority.SIDECAR_OBSERVE_ONLY):
        assert a in RunAuthority.RUNNABLE


def test_unbounded_context_reports_unbounded():
    ctx = RunContext(max_steps=None, max_duration_s=None)
    assert not ctx.is_bounded


def test_boundary_roundtrip():
    ctx = RunContext(max_steps=10, max_duration_s=5.0)
    b = ctx.boundary()
    assert isinstance(b, RunBoundary)
    assert b.max_steps == 10 and b.is_bounded


def test_to_dict_exposes_derived_flags():
    d = RunContext(mode=RunMode.MONTH_SCALE_PLAN).to_dict()
    assert d["is_plan_only"] is True
    assert "requires_governance" in d and "is_bounded" in d
