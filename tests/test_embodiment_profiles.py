"""EmbodimentProfileRegistry: bounded simulation profiles, no real-world body."""

from __future__ import annotations

import pytest

from solaris_ai_nn.motor_membrane import (
    EmbodimentProfile,
    EmbodimentProfileName,
    EmbodimentProfileRegistry,
)


def test_registry_has_no_real_world_profile():
    reg = EmbodimentProfileRegistry()
    assert reg.has_real_world_profile() is False
    assert all(not p.real_world_authority for p in reg.profiles.values())


def test_all_named_profiles_present():
    reg = EmbodimentProfileRegistry()
    for name in EmbodimentProfileName.ALL:
        assert reg.get(name) is not None


def test_require_unknown_raises():
    with pytest.raises(KeyError):
        EmbodimentProfileRegistry().require("real_robot")


def test_profile_forces_no_real_world_authority():
    p = EmbodimentProfile("x", "y", real_world_authority=True)
    assert p.real_world_authority is False
    assert p.to_dict()["simulation_or_dry_run_only"] is True


def test_dry_run_profile_is_dry_run():
    reg = EmbodimentProfileRegistry()
    assert reg.require(EmbodimentProfileName.DRY_RUN_MOTOR).dry_run is True


def test_plan_only_profile_starts_no_body():
    reg = EmbodimentProfileRegistry()
    p = reg.require(EmbodimentProfileName.PILOT3_LIMITED_EMBODIMENT_PLAN)
    assert p.plan_only is True
    assert p.enable_gridworld is False


def test_snapshot_reports_no_real_world():
    snap = EmbodimentProfileRegistry().snapshot()
    assert snap["has_real_world_profile"] is False
