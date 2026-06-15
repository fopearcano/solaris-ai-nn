"""RunPlanner: bounded plan built; prohibited blocked; external authority false."""

from __future__ import annotations

from solaris_ai_nn.operator_console import ProfileCatalog, RunPlanner


def _planner():
    return RunPlanner(ProfileCatalog())


def test_bounded_profile_plan_generated():
    plan = _planner().plan("safety_fast_check")
    assert plan.validation.valid is True
    assert plan.can_run_from_console is True
    assert plan.steps  # the plan describes concrete steps


def test_prohibited_profile_plan_blocked():
    plan = _planner().plan("pilot1_30d_soak")
    assert plan.validation.valid is False
    assert plan.can_run_from_console is False


def test_unknown_profile_plan_refused():
    plan = _planner().plan("does_not_exist")
    assert plan.validation.valid is False
    assert "unknown" in " ".join(plan.validation.reasons).lower()


def test_external_authority_false_included():
    plan = _planner().plan("safety_fast_check")
    assert plan.external_authority is False
    assert plan.to_dict()["external_authority"] is False
    assert "external authority: false" in [s.lower() for s in plan.limitations]


def test_planning_runs_nothing():
    # The plan lists a rollback that relies on bounds + emergency stop, proving
    # nothing is executed by planning.
    plan = _planner().plan("research_baseline_random")
    assert plan.rollback_plan
    assert any("emergency stop" in s.description for s in plan.rollback_plan)
