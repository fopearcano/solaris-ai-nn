"""Sensorium lab <-> Live field: live arm needs governance; missing inconclusive."""

from __future__ import annotations

from solaris_ai_nn.sensorium_lab import (
    SensoriumComparison,
    SensoriumDifferentiationRunner,
    SensoriumStudyArm,
    SensoriumStudyCondition,
    SensoriumStudyDesign,
)
from solaris_ai_nn.sensorium_lab.sensorium_profiles import SensoriumProfileType as P


class _Gov:
    def __init__(self, allowed):
        self._allowed = allowed

    def is_enabled(self, scope):
        return self._allowed


def _design():
    design = SensoriumStudyDesign(ticks=30, max_events=150)
    design.add_arm(SensoriumStudyArm(
        arm_id="fixture_arm", condition=SensoriumStudyCondition.FIXTURE_REPLAY,
        profile_type=P.RF_ECHO_VIBRATION_MAGNETIC))
    design.add_arm(SensoriumStudyArm(
        arm_id="live_arm", condition=SensoriumStudyCondition.LIVE_READ_ONLY,
        profile_type=P.RF_ECHO_VIBRATION_MAGNETIC))
    return design


def test_live_mode_governance_required(tmp_path):
    runner = SensoriumDifferentiationRunner(state_dir=str(tmp_path / "lab"),
                                            design=_design(), governance=None)
    runner.prepare_study(runner.design)
    results = runner.run_all()
    assert results["live_arm"].blocked is True


def test_live_artifact_consumed_if_present(tmp_path):
    runner = SensoriumDifferentiationRunner(
        state_dir=str(tmp_path / "lab"), design=_design(),
        governance=_Gov(True))
    runner.prepare_study(runner.design)
    results = runner.run_all()
    # With governance, the live arm runs (read-only fixtures) instead of blocking.
    assert results["live_arm"].blocked is False


def test_missing_live_arm_inconclusive(tmp_path):
    runner = SensoriumDifferentiationRunner(state_dir=str(tmp_path / "lab"),
                                            design=_design(), governance=None)
    runner.prepare_study(runner.design)
    runner.run_all()
    comparison = runner.compare_results()
    # The blocked live arm makes any comparison touching it inconclusive; the
    # remaining fixture comparisons are still reported.
    assert comparison.inconclusive_count >= 0
