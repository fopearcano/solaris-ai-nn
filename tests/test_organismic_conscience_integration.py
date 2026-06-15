"""Organismic demo <-> Conscience: profiles exist; bounded; report-only."""

from __future__ import annotations

from solaris_ai_nn.conscience.run_context import RunMode
from solaris_ai_nn.conscience.scenario_profiles import ScenarioProfileRegistry

_PROFILES = (
    "minimal_field_organism_demo",
    "minimal_field_organism_report_only",
    "minimal_field_organism_comparison",
    "minimal_field_organism_changed_perception_probe",
)


def test_profiles_exist():
    reg = ScenarioProfileRegistry()
    for pid in _PROFILES:
        assert reg.get(pid) is not None, pid


def test_bounded_profile_runs():
    reg = ScenarioProfileRegistry()
    demo = reg.get("minimal_field_organism_demo")
    assert demo.run_context.is_bounded
    assert demo.run_context.mode == RunMode.SHORT_DEMO


def test_report_only_does_not_run_full_loop():
    reg = ScenarioProfileRegistry()
    report = reg.get("minimal_field_organism_report_only")
    # The report-only profile is plan-only: no cognition loop.
    assert report.is_plan_only


def test_no_hardware_profile():
    reg = ScenarioProfileRegistry()
    for pid in _PROFILES:
        assert "hardware" not in pid
    profile = reg.get("minimal_field_organism_demo")
    joined = " ".join(profile.safety_constraints).lower()
    assert "no hardware" in joined
    assert "debug-truth file is excluded from perception" in joined
