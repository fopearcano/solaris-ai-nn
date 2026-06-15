"""NoveltyAppetiteRegulator: fatigue; starvation; recurring novelty -> invariant."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.perceptual_metabolism import NoveltyAppetiteRegulator
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.plural_sensorium.sensory_field import SensoryFieldState


def _field(novelty, noise=0.1):
    return SensoryFieldState(
        tick=1, active_modalities=["radio_frequency"], active_receptors=1,
        field_pressure=0.5, noise_pressure=noise, absence_pressure=0.1,
        novelty_pressure=novelty, rhythm_pressure=0.3, cross_modal_pressure=0.2,
        uncertainty_pressure=0.1, saturation=0.2, fatigue=0.2, stability=0.7,
        dominant_modality="radio_frequency", neglected_modality=None,
        field_tensions=[])


def _sensorium(tmp_path):
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "ps"))
    path = os.path.join(str(tmp_path), "rf.jsonl")
    with open(path, "w") as fh:
        for i in range(8):
            fh.write(json.dumps({"modality": "alien_rf", "power": 0.7,
                                 "ts": float(i)}) + "\n")
    rt.add_feeder(fixture_feeder("rf_feed", path, "alien_rf"))
    rt.run_bounded(max_polls=1)
    return rt


def test_novelty_fatigue_detected(tmp_path):
    reg = NoveltyAppetiteRegulator()
    rt = _sensorium(tmp_path)
    state = None
    for _ in range(10):
        state = reg.update(rt, field_state=_field(0.9, noise=0.9))
    assert state.novelty_fatigue > 0.0 or "noise" in state.recommendation


def test_novelty_starvation_detected(tmp_path):
    reg = NoveltyAppetiteRegulator()
    rt = _sensorium(tmp_path)
    state = reg.update(rt, field_state=_field(0.0))
    assert state.novelty_starvation == 1.0
    assert state.recommendation == "raise_novelty_appetite"


def test_recurring_novelty_becomes_invariant(tmp_path):
    # A stable repeated RF source produces invariant candidates -> conversion.
    reg = NoveltyAppetiteRegulator()
    rt = _sensorium(tmp_path)
    state = reg.update(rt, field_state=_field(0.4))
    assert len(rt.invariants.candidates) >= 1
    assert 0.0 <= state.novelty_to_invariant_rate <= 1.0
