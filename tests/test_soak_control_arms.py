"""Soak control arms: configure, missing inconclusive, live requires governance."""

from __future__ import annotations

from solaris_ai_nn.developmental_soak import (
    ControlArmConfig,
    ControlArmId,
    SoakControlArm,
)


def test_control_arms_configure():
    for arm_id in ControlArmId.ALL:
        cfg = ControlArmConfig.for_arm(arm_id)
        assert cfg.arm_id == arm_id
        assert cfg.to_dict()["arm_id"] == arm_id


def test_missing_arm_inconclusive():
    arm = SoakControlArm()
    # No structural modules in the stack -> no_metabolism arm is unavailable.
    cfg = ControlArmConfig.for_arm(ControlArmId.NO_PERCEPTUAL_METABOLISM)
    result = arm.run(cfg, module_stack={"perceptual_metabolism": {}},
                     build_runtime=None)
    assert result.available is False
    assert result.growth_status == "inconclusive"


def test_live_arm_requires_governance():
    arm = SoakControlArm()
    cfg = ControlArmConfig.for_arm(ControlArmId.LIVE_READ_ONLY_IF_AVAILABLE)
    assert cfg.requires_governance is True
    result = arm.run(cfg, module_stack={"plural_sensorium": {},
                                        "semiogenesis": {}},
                     build_runtime=lambda *a, **k: None,
                     governance_approved=False)
    assert result.available is False
    assert "governance" in result.note.lower()


def test_configured_but_not_run_without_builder():
    arm = SoakControlArm()
    cfg = ControlArmConfig.for_arm(ControlArmId.FULL_STACK)
    result = arm.run(cfg, module_stack={"plural_sensorium": {},
                                        "semiogenesis": {}}, build_runtime=None)
    assert result.available is True
    assert result.ran is False
