"""EmbodimentPreflightRunner: passes a valid sandbox; fails unsafe setups."""

from __future__ import annotations

from solaris_ai_nn.motor_membrane import EmbodimentSandboxRuntime
from solaris_ai_nn.pilot3 import (
    EmbodimentPreflightRunner,
    Pilot3Config,
    Pilot3SoakSafetyValidator,
)


def _runtime(state_dir):
    rt = EmbodimentSandboxRuntime(state_dir=state_dir, seed=4)
    rt.initialize()
    return rt


def test_passes_valid_sandbox(tmp_path):
    cfg = Pilot3Config(base_dir=str(tmp_path)).ensure_dirs()
    rt = _runtime(cfg.state_dir)
    result = EmbodimentPreflightRunner(config=cfg).run(motor_membrane=rt)
    assert result.passed is True
    assert result.to_dict()["real_world_authority"] is False


def test_fails_real_actuator(tmp_path):
    cfg = Pilot3Config(base_dir=str(tmp_path)).ensure_dirs()
    rt = _runtime(cfg.state_dir)

    class _RealActuator:
        name = "robot_arm_driver"

    rt._actuators.append(_RealActuator())
    result = EmbodimentPreflightRunner(config=cfg).run(motor_membrane=rt)
    assert result.passed is False
    names = {c.name for c in result.checks if not c.passed}
    assert "no_real_world_actuator" in names


def test_fails_source_modification_authority():
    v = Pilot3SoakSafetyValidator()
    # The safety validator flags source modification as unsafe (preflight
    # depends on this denial).
    assert v.validate_operation("modify source").safe is False


def test_writes_report(tmp_path):
    cfg = Pilot3Config(base_dir=str(tmp_path)).ensure_dirs()
    rt = _runtime(cfg.state_dir)
    runner = EmbodimentPreflightRunner(config=cfg)
    result = runner.run_and_write(motor_membrane=rt)
    import os
    assert os.path.exists(os.path.join(str(tmp_path),
                                       "embodiment_preflight.md"))
    assert os.path.exists(os.path.join(str(tmp_path),
                                       "embodiment_preflight.json"))
    assert result.passed is True
