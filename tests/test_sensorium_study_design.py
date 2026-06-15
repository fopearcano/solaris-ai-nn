"""SensoriumStudyDesign: arms serialize; bounded defaults; live needs gov."""

from __future__ import annotations

from solaris_ai_nn.sensorium_lab import (
    SensoriumStudyArm,
    SensoriumStudyCondition,
    SensoriumStudyDesign,
    default_study_design,
)


def test_study_arms_serialize():
    design = default_study_design()
    data = design.to_dict()
    assert data["arms"]
    assert all("condition" in a for a in data["arms"])


def test_bounded_defaults():
    design = SensoriumStudyDesign()
    assert design.ticks > 0
    assert design.max_events > 0


def test_live_arms_require_governance():
    arm = SensoriumStudyArm(
        arm_id="live", condition=SensoriumStudyCondition.LIVE_READ_ONLY,
        profile_type="rf_echo_vibration_magnetic")
    assert arm.live is True
    assert arm.requires_governance is True


def test_unknown_condition_rejected():
    try:
        SensoriumStudyArm(arm_id="x", condition="bogus", profile_type="y")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_default_study_has_human_nonhuman_mixed():
    ids = {a.arm_id for a in default_study_design().arms}
    assert {"human_like", "non_human", "mixed"} <= ids
