"""Architecture <-> Conscience: profiles exist, plan-only, no source change."""

from __future__ import annotations

from solaris_ai_nn.conscience import RunMode, ScenarioProfileRegistry

_PROFILES = ("architecture_inventory", "architecture_review",
             "architecture_roadmap_compile", "architecture_snapshot",
             "architecture_changelog_plan")


def test_architecture_profiles_exist():
    ids = set(ScenarioProfileRegistry().ids())
    assert set(_PROFILES) <= ids


def test_profiles_do_not_run_cognition_loop():
    reg = ScenarioProfileRegistry()
    for name in _PROFILES:
        ctx = reg.get(name).run_context
        assert ctx.mode == RunMode.MONTH_SCALE_PLAN
        assert ctx.max_steps is None


def test_profiles_do_not_modify_source_code():
    reg = ScenarioProfileRegistry()
    for name in _PROFILES:
        constraints = " ".join(reg.get(name).safety_constraints).lower()
        assert "no source-code modification" in constraints
        assert "no auto-deletion" in constraints
        assert "safety-critical modules cannot be pruned" in constraints
