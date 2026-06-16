"""Research cycle scenario profiles exist with the right safety constraints."""

from __future__ import annotations

from solaris_ai_nn.conscience.scenario_profiles import ScenarioProfileRegistry

_PROFILES = ("research_cycle_status", "research_cycle_decision_gate",
             "research_cycle_evidence_ledger", "research_cycle_artifact_graph",
             "research_cycle_next_action", "research_cycle_blocked")


def test_profiles_registered():
    reg = ScenarioProfileRegistry()
    for pid in _PROFILES:
        assert reg.get(pid) is not None


def test_profiles_have_research_cycle_module():
    reg = ScenarioProfileRegistry()
    profile = reg.require("research_cycle_status")
    assert "research_cycle" in profile.enabled_modules


def test_profiles_declare_no_execution_constraints():
    reg = ScenarioProfileRegistry()
    constraints = " ".join(reg.require("research_cycle_status").safety_constraints)
    assert "no Git/GitHub call" in constraints
    assert "never auto-approved" in constraints
    assert "critical safety blocker cannot be bypassed" in constraints
