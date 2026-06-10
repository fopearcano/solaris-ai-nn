"""Tests for the staged soak plan."""

from __future__ import annotations

from solaris_ai_nn.ops.soak_plan import SoakPlanBuilder


def test_default_plan_does_not_launch_long_runs(tmp_path):
    plan = SoakPlanBuilder().build()
    assert len(plan.stages) == 5
    # No stage ever auto-launches; only stage 1 is included by default.
    assert all(stage.auto_launch is False for stage in plan.stages)
    included = plan.included_stages()
    assert len(included) == 1
    assert "5-minute" in included[0].name


def test_long_stages_require_explicit_inclusion():
    plan = SoakPlanBuilder().build()
    by_name = {s.name: s for s in plan.stages}
    assert by_name["24-hour soak"].requires_flag is True
    assert by_name["24-hour soak"].included is False
    assert by_name["30-day soak"].included is False
    flagged = SoakPlanBuilder(include_24h=True, include_30d=True).build()
    by_name = {s.name: s for s in flagged.stages}
    assert by_name["24-hour soak"].included is True
    assert by_name["30-day soak"].included is True
    # Even when included, nothing auto-launches.
    assert all(s.auto_launch is False for s in flagged.stages)


def test_markdown_and_json_plan_generated(tmp_path):
    plan = SoakPlanBuilder().build()
    paths = plan.write(tmp_path)
    md = (tmp_path / "soak_plan.md").read_text()
    assert md.startswith("# Solaris-AI-NN staged soak plan")
    assert "requires explicit flag" in md
    assert "No stage is launched" in plan.note
    assert (tmp_path / "soak_plan.json").exists()
