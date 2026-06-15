"""Organismic demo <-> Plural sensorium: runtime used; field persists; baseline."""

from __future__ import annotations

from solaris_ai_nn.organismic_demo import (
    MinimalFieldOrganismRunner,
    OrganismicDemoConfig,
)
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime


def _runner(tmp_path):
    runner = MinimalFieldOrganismRunner(
        state_dir=str(tmp_path / "d"),
        config=OrganismicDemoConfig(ticks=120, seed=7))
    runner.run()
    return runner


def test_plural_sensorium_runtime_used(tmp_path):
    runner = _runner(tmp_path)
    assert isinstance(runner.runtime, PluralSensoriumRuntime)


def test_receptors_updated(tmp_path):
    runner = _runner(tmp_path)
    assert runner.runtime.receptors
    assert any(r.event_count > 0 for r in runner.runtime.receptors.values())


def test_sensory_field_persisted(tmp_path):
    runner = _runner(tmp_path)
    # The continuous field advanced across many ticks.
    assert runner.runtime.sensory_field.tick > 1
    assert runner.runtime.sensory_field.continuity.tick_count > 1


def test_baseline_shift_detected(tmp_path):
    runner = _runner(tmp_path)
    # The scenario injects a mid-run magnetic anomaly -> a baseline shift.
    assert len(runner.runtime.baseline_shifts) >= 1
