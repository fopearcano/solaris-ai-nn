"""SensoriumDifferentiationRunner: fixture runs; live blocked without gov."""

from __future__ import annotations

from solaris_ai_nn.sensorium_lab import (
    SensoriumDifferentiationRunner,
    SensoriumStudyArm,
    SensoriumStudyCondition,
    SensoriumStudyDesign,
    default_study_design,
)
from solaris_ai_nn.sensorium_lab.sensorium_profiles import SensoriumProfileType as P


def test_fixture_study_runs(tmp_path):
    design = default_study_design()
    design.ticks = 40
    runner = SensoriumDifferentiationRunner(state_dir=str(tmp_path / "lab"),
                                            design=design)
    assert runner.prepare_study(design)
    results = runner.run_all()
    assert len(results) == len(design.arms)
    assert all(not r.blocked for r in results.values())


def test_live_study_blocked_without_governance(tmp_path):
    design = SensoriumStudyDesign(ticks=30, max_events=150)
    design.add_arm(SensoriumStudyArm(
        arm_id="live", condition=SensoriumStudyCondition.LIVE_READ_ONLY,
        profile_type=P.RF_ECHO_VIBRATION_MAGNETIC))
    runner = SensoriumDifferentiationRunner(state_dir=str(tmp_path / "lab"),
                                            design=design, governance=None)
    runner.prepare_study(design)
    results = runner.run_all()
    assert results["live"].blocked is True
    assert any("governance" in r for r in results["live"].reasons)


def test_fixture_arms_continue_when_live_blocked(tmp_path):
    design = SensoriumStudyDesign(ticks=30, max_events=150)
    design.add_arm(SensoriumStudyArm(
        arm_id="fixture", condition=SensoriumStudyCondition.FIXTURE_REPLAY,
        profile_type=P.RF_ECHO_VIBRATION_MAGNETIC))
    design.add_arm(SensoriumStudyArm(
        arm_id="live", condition=SensoriumStudyCondition.LIVE_READ_ONLY,
        profile_type=P.RF_ECHO_VIBRATION_MAGNETIC))
    runner = SensoriumDifferentiationRunner(state_dir=str(tmp_path / "lab"),
                                            design=design)
    runner.prepare_study(design)
    results = runner.run_all()
    assert results["live"].blocked is True
    assert results["fixture"].blocked is False
    assert results["fixture"].signature is not None


def test_unbounded_study_refused(tmp_path):
    design = SensoriumStudyDesign(ticks=0, max_events=0)
    runner = SensoriumDifferentiationRunner(state_dir=str(tmp_path / "lab"))
    assert runner.prepare_study(design) is False
