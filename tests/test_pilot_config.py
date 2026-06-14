"""Pilot-1 config: defaults, labelling, governance gating, path confinement."""

from __future__ import annotations

import pytest

from solaris_ai_nn.pilot1 import PilotAuthority, PilotConfig, PilotMode


def test_default_is_plan_only(tmp_path):
    cfg = PilotConfig(base_dir=str(tmp_path))
    assert cfg.mode == PilotMode.PLAN_ONLY
    assert cfg.is_simulated and not cfg.is_real_time
    assert not cfg.requires_governance


def test_unknown_mode_and_authority_rejected(tmp_path):
    with pytest.raises(ValueError):
        PilotConfig(mode="nope", base_dir=str(tmp_path))
    with pytest.raises(ValueError):
        PilotConfig(authority="nope", base_dir=str(tmp_path))


def test_real_modes_require_governance(tmp_path):
    for mode in (PilotMode.TWENTY_FOUR_HOUR_REAL, PilotMode.SEVEN_DAY_REAL,
                 PilotMode.THIRTY_DAY_REAL, PilotMode.MULTI_MONTH_REAL):
        cfg = PilotConfig(mode=mode, base_dir=str(tmp_path))
        assert cfg.requires_governance
        assert cfg.is_real_time
        assert cfg.required_scope


def test_time_label_distinguishes_simulated_and_real(tmp_path):
    sim = PilotConfig(mode=PilotMode.DRY_RUN_SIMULATED, base_dir=str(tmp_path))
    real = PilotConfig(mode=PilotMode.THIRTY_DAY_REAL, base_dir=str(tmp_path))
    assert "SIMULATED" in sim.time_label and "not a real month" in sim.time_label
    assert "REAL-TIME" in real.time_label


def test_paths_are_inside_base(tmp_path):
    cfg = PilotConfig(base_dir=str(tmp_path))
    env = cfg.environment()
    assert env.is_inside(env.state_dir)
    assert not env.is_inside("/etc/passwd")


def test_llm_adapter_off_by_default(tmp_path):
    cfg = PilotConfig(base_dir=str(tmp_path))
    assert cfg.enable_llm_adapter is False


def test_roundtrip(tmp_path):
    cfg = PilotConfig(mode=PilotMode.SEVEN_DAY_REAL, base_dir=str(tmp_path))
    clone = PilotConfig.from_dict(cfg.to_dict())
    assert clone.mode == cfg.mode and clone.authority == cfg.authority
