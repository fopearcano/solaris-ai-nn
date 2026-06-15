"""Metabolism wires into Sensory Homeostasis and the Conscience spine/profiles."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.conscience.scenario_profiles import ScenarioProfileRegistry
from solaris_ai_nn.conscience.spine import SpinePhase
from solaris_ai_nn.perceptual_metabolism import (
    PerceptualNeedModel,
    SensoryHomeostasisRegulator,
)
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder


def _sensorium(tmp_path):
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "ps"))
    path = os.path.join(str(tmp_path), "rf.jsonl")
    with open(path, "w") as fh:
        for i in range(10):
            fh.write(json.dumps({"modality": "alien_rf", "power": 0.6,
                                 "ts": float(i)}) + "\n")
    rt.add_feeder(fixture_feeder("rf_feed", path, "alien_rf"))
    rt.run_bounded(max_polls=1)
    return rt


def test_needs_drive_homeostatic_regulation(tmp_path):
    rt = _sensorium(tmp_path)
    field_state = rt.sensory_field.state()
    receptors = list(rt.receptors.values())

    needs = PerceptualNeedModel()
    needs.update(field_state, receptors, tick=0)
    assert needs.needs  # perceptual pressures derived from the field

    state = SensoryHomeostasisRegulator().regulate(field_state, receptors)
    # Homeostatic regulation produces internal recommendations only.
    data = state.to_dict()
    assert "no external" in data["note"]
    assert isinstance(state.recommendations, list)


def test_conscience_phase_exists_in_order():
    assert SpinePhase.PERCEPTUAL_METABOLISM_UPDATE == "perceptual_metabolism_update"
    assert SpinePhase.PERCEPTUAL_METABOLISM_UPDATE in SpinePhase.ORDER
    # It runs after the sensory field update and before stimulus ingestion.
    order = SpinePhase.ORDER
    assert (order.index(SpinePhase.SENSORY_FIELD_UPDATE)
            < order.index(SpinePhase.PERCEPTUAL_METABOLISM_UPDATE)
            < order.index(SpinePhase.STIMULUS_INGESTION))


def test_metabolism_profiles_exist_and_are_bounded():
    reg = ScenarioProfileRegistry()
    metabolism_ids = [pid for pid in reg.ids()
                      if pid.startswith("perceptual_metabolism")]
    assert len(metabolism_ids) >= 6
    for pid in metabolism_ids:
        profile = reg.require(pid)
        # Every runnable profile is bounded (max_runtime_s or a plan-only ctx).
        assert profile.max_runtime_s and profile.max_runtime_s > 0
        constraints = " ".join(profile.safety_constraints)
        assert "not feelings" in constraints
        assert "no hardware/feeder control" in constraints
