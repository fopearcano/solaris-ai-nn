"""Tests for the pilot profiles."""

from __future__ import annotations

import pytest

from solaris_ai_nn.pilot.profiles import (
    UNIVERSALLY_FORBIDDEN_OUTPUTS,
    PilotProfile,
    PilotProfileRegistry,
    PilotProfileType,
)


def test_required_profiles_exist():
    registry = PilotProfileRegistry.default()
    assert registry.list_profiles() == sorted([
        "simulated", "read_only_stream", "solaris_sidecar_observe"])
    for name in PilotProfileType.ALL:
        profile = registry.get(name)
        assert profile.profile_type == name
        assert profile.default_max_steps > 0
        assert profile.required_permissions
        assert profile.required_artifacts
        assert profile.expected_evaluation_protocols
        assert profile.emergency_stop_required


def test_simulated_is_default():
    registry = PilotProfileRegistry.default()
    assert PilotProfileType.DEFAULT == "simulated"
    assert registry.default_profile().profile_type == "simulated"
    assert registry.default_profile().safety_mode == "simulation_only"


def test_read_only_stream_forbids_actions():
    profile = PilotProfileRegistry.default().get("read_only_stream")
    assert profile.allowed_actions == []  # no external actions, at all
    assert profile.safety_mode == "observe_only"
    for output in UNIVERSALLY_FORBIDDEN_OUTPUTS:
        assert profile.forbids(output), output


def test_sidecar_observe_forbids_committed_actions():
    profile = PilotProfileRegistry.default().get("solaris_sidecar_observe")
    assert profile.allowed_actions == []
    assert profile.forbids("committed_solaris_actions")
    assert profile.safety_mode == "sidecar_observe_only"


def test_no_profile_may_allow_real_world_action():
    registry = PilotProfileRegistry.default()
    for name in registry.list_profiles():
        profile = registry.get(name)
        assert profile.forbids("real_world_actuation"), name
        assert profile.forbids("network_calls"), name
        assert profile.forbids("browser_automation"), name

    # A profile that fails to forbid them cannot even be registered.
    rogue = PilotProfile(name="rogue", profile_type="rogue",
                         safety_mode="none", forbidden_outputs=[])
    with pytest.raises(ValueError):
        registry.register(rogue)


def test_unknown_profile_rejected():
    with pytest.raises(ValueError):
        PilotProfileRegistry.default().get("autonomous")
