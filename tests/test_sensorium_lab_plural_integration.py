"""Sensorium lab <-> Plural sensorium: runtime used; receptors + field present."""

from __future__ import annotations

from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime
from solaris_ai_nn.sensorium_lab import (
    SensoriumDifferentiationRunner,
    SensoriumStudyArm,
    SensoriumStudyCondition,
    SensoriumStudyDesign,
)
from solaris_ai_nn.sensorium_lab.sensorium_profiles import SensoriumProfileType as P


def _arm(tmp_path):
    design = SensoriumStudyDesign(ticks=40, max_events=200)
    design.add_arm(SensoriumStudyArm(
        arm_id="non_human", condition=SensoriumStudyCondition.NON_HUMAN_ONLY,
        profile_type=P.RF_ECHO_VIBRATION_MAGNETIC))
    runner = SensoriumDifferentiationRunner(state_dir=str(tmp_path / "lab"),
                                            design=design)
    runner.prepare_study(design)
    runner.run_all()
    return runner.arm_results["non_human"]


def test_plural_sensorium_runtime_used(tmp_path):
    r = _arm(tmp_path)
    assert isinstance(r.runtime, PluralSensoriumRuntime)


def test_receptor_states_included(tmp_path):
    r = _arm(tmp_path)
    assert r.runtime.receptors
    assert any(rec.event_count > 0 for rec in r.runtime.receptors.values())


def test_sensory_field_included(tmp_path):
    r = _arm(tmp_path)
    assert r.runtime.sensory_field.tick > 1
    assert r.signature.field_pressure_profile
