"""Pilot3Config: real_world_authority always false; modes/conditions exist."""

from __future__ import annotations

import pytest

from solaris_ai_nn.pilot3 import (
    EmbodimentCondition,
    Pilot3Authority,
    Pilot3Config,
    Pilot3Mode,
)


def test_real_world_authority_always_false():
    c = Pilot3Config(mode=Pilot3Mode.GRIDWORLD_SHORT,
                     authority=Pilot3Authority.SANDBOX_ONLY,
                     condition=EmbodimentCondition.GRIDWORLD_BODY)
    assert c.real_world_authority is False


def test_invalid_real_world_config_rejected():
    with pytest.raises(ValueError):
        Pilot3Config(real_world_authority=True)
    with pytest.raises(ValueError):
        Pilot3Config(authority=Pilot3Authority.FORBIDDEN_REAL_WORLD)
    with pytest.raises(ValueError):
        Pilot3Config(metadata={"real_world_actuation": True})


def test_all_modes_exist():
    for mode in Pilot3Mode.ALL:
        assert isinstance(mode, str)
    assert {"plan_only", "firewall_preflight", "dry_run_motor_trace",
            "gridworld_short", "gridworld_soak_simulated",
            "mixed_sensory_gridworld_short", "mixed_sensory_gridworld_soak",
            "comparative_analysis"} == set(Pilot3Mode.ALL)


def test_all_conditions_exist():
    assert {"no_body", "read_only_perception", "gridworld_body",
            "mixed_sensory_gridworld", "dry_run_motor"} == \
        set(EmbodimentCondition.ALL)


def test_soak_must_be_bounded():
    # A soak with no step/time bound is rejected.
    with pytest.raises(ValueError):
        Pilot3Config(mode=Pilot3Mode.GRIDWORLD_SOAK_SIMULATED,
                     authority=Pilot3Authority.SANDBOX_ONLY,
                     max_steps=None, max_duration_s=None)


def test_required_scope_mapping():
    c = Pilot3Config(mode=Pilot3Mode.GRIDWORLD_SHORT,
                     authority=Pilot3Authority.SANDBOX_ONLY)
    assert c.required_scope == "enable_pilot3_gridworld_short"


def test_dirs_and_roundtrip(tmp_path):
    c = Pilot3Config(base_dir=str(tmp_path)).ensure_dirs()
    assert c.sandbox_root_approved(c.sandbox_dir) is True
    assert c.sandbox_root_approved("/etc/passwd") is False
    d = Pilot3Config.from_dict(c.to_dict())
    assert d.real_world_authority is False
