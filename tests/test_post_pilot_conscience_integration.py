"""Post-pilot <-> Conscience: the analysis profile exists and runs no loop."""

from __future__ import annotations

from solaris_ai_nn.conscience import (
    ConscienceOrchestrator,
    ScenarioProfileRegistry,
)
from solaris_ai_nn.governance.policy import GovernancePolicy


def test_post_pilot_analysis_profile_exists():
    reg = ScenarioProfileRegistry()
    assert "post_pilot_analysis" in reg.ids()


def test_profile_is_plan_only_no_cognition_loop():
    reg = ScenarioProfileRegistry()
    profile = reg.require("post_pilot_analysis")
    assert profile.is_plan_only


def test_profile_runs_no_steps_and_no_mutation(tmp_path):
    gov = GovernancePolicy()  # enable_pilot1 granted by default
    profile = ScenarioProfileRegistry().require("post_pilot_analysis")
    profile.run_context.state_dir = str(tmp_path)
    orch = ConscienceOrchestrator(governance=gov, governance_approved=True)
    orch.configure(profile)
    orch.initialize()
    out = orch.run()
    assert out.get("plan_only") is True
    assert orch.step_count == 0  # cognition loop never ran


def test_profile_declares_read_only_constraints():
    profile = ScenarioProfileRegistry().require("post_pilot_analysis")
    joined = " ".join(profile.safety_constraints).lower()
    assert "read-only" in joined or "no cognition loop" in joined
    assert "does not mutate" in joined
