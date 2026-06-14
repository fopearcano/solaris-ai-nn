"""SafetyInvariantDashboard: JSON + Markdown; critical failures displayed."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.safety_invariants import (
    SafetyInvariantDashboard,
    SafetyInvariantRegistry,
    SafetyInvariantRunner,
)


def _bundle(ctx):
    return SafetyInvariantRunner(registry=SafetyInvariantRegistry()).run_fast(
        ctx)


def test_dashboard_json_generated(tmp_path):
    reg = SafetyInvariantRegistry()
    dash = SafetyInvariantDashboard(base_dir=str(tmp_path)).build_and_write(
        registry_snapshot=reg.snapshot(),
        fast_bundle=_bundle({"motor_membrane": {"real_world_authority": False,
                                                "firewall_enabled": True,
                                                "firewall_can_be_disabled":
                                                False,
                                                "current_authority":
                                                "simulation_only"}}))
    assert os.path.exists(os.path.join(str(tmp_path), "SAFETY_DASHBOARD.json"))
    assert "recommended_next_action" in dash


def test_dashboard_markdown_generated(tmp_path):
    reg = SafetyInvariantRegistry()
    SafetyInvariantDashboard(base_dir=str(tmp_path)).build_and_write(
        registry_snapshot=reg.snapshot(), fast_bundle=_bundle({}))
    assert os.path.exists(os.path.join(str(tmp_path), "SAFETY_DASHBOARD.md"))


def test_critical_failures_displayed(tmp_path):
    reg = SafetyInvariantRegistry()
    bundle = _bundle({"motor_membrane": {"real_world_authority": True,
                                         "firewall_enabled": True}})
    d = SafetyInvariantDashboard(base_dir=str(tmp_path)).build(
        registry_snapshot=reg.snapshot(), full_bundle=bundle)
    assert d["critical_failures"] >= 1
    assert "block escalation" in d["recommended_next_action"]


def test_recommended_action_safe_when_clean(tmp_path):
    reg = SafetyInvariantRegistry()
    d = SafetyInvariantDashboard(base_dir=str(tmp_path)).build(
        registry_snapshot=reg.snapshot(),
        red_team_summary={"all_blocked": True},
        boundary_summary={"all_held": True})
    assert "safe to continue" in d["recommended_next_action"]
