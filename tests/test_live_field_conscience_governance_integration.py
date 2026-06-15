"""Live field <-> Conscience + Governance: profiles; governed needs approval."""

from __future__ import annotations

from solaris_ai_nn.conscience.scenario_profiles import ScenarioProfileRegistry
from solaris_ai_nn.governance.permissions import PermissionScope, PermissionSet
from solaris_ai_nn.governance.policy import GovernancePolicy

_PROFILES = ("live_field_preflight", "live_field_report_only",
             "live_field_fixture_fallback",
             "live_field_changed_perception_probe", "live_field_comparison",
             "live_field_short_governed")


def test_profiles_exist():
    reg = ScenarioProfileRegistry()
    for pid in _PROFILES:
        assert reg.get(pid) is not None, pid


def test_governed_profile_requires_approval():
    reg = ScenarioProfileRegistry()
    governed = reg.get("live_field_short_governed")
    assert "enable_live_field_read_only_pilot" in \
        governed.governance_requirements


def test_report_only_profile_allowed():
    ps = PermissionSet.default()
    assert ps.allows(PermissionScope.ENABLE_LIVE_FIELD_REPORT)
    assert ps.allows(PermissionScope.ENABLE_LIVE_FIELD_PREFLIGHT)


def test_live_pilot_scope_requires_approval():
    ps = PermissionSet.default()
    # The live read-only pilot is not granted outright; it needs approval.
    assert not ps.allows(PermissionScope.ENABLE_LIVE_FIELD_READ_ONLY_PILOT)


def test_no_hardware_profile():
    reg = ScenarioProfileRegistry()
    for pid in reg.ids():
        if pid.startswith("live_field"):
            assert "hardware" not in pid
    profile = reg.get("live_field_short_governed")
    joined = " ".join(profile.safety_constraints).lower()
    assert "no feeder auto-start" in joined
