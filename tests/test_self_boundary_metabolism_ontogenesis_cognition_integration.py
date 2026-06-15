"""Self-boundary: metabolism affects perspective; concepts/signs/sims handled."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.perceptual_ontogenesis import PerceptualOntogenesisRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.self_boundary import BoundaryZone
from solaris_ai_nn.semiogenesis import SemiogenesisRuntime
from solaris_ai_nn.sensorium_cognition import SensoriumCognitionRuntime
from solaris_ai_nn.self_boundary import SelfBoundaryRuntime


def _stack(tmp_path):
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "ps"))
    for mod in ("alien_rf", "alien_vibration"):
        path = os.path.join(str(tmp_path), f"{mod}.jsonl")
        with open(path, "w") as fh:
            for i in range(12):
                fh.write(json.dumps({"modality": mod, "v": 0.6,
                                     "ts": float(i)}) + "\n")
        rt.add_feeder(fixture_feeder(f"{mod}_feed", path, mod))
    rt.run_bounded(max_polls=3)
    ont = PerceptualOntogenesisRuntime(state_dir=str(tmp_path / "o"),
                                       sensorium=rt, max_ticks=6)
    ont.run_bounded()
    sem = SemiogenesisRuntime(state_dir=str(tmp_path / "s"), ontogenesis=ont,
                              max_ticks=5)
    sem.run_bounded()
    cog = SensoriumCognitionRuntime(state_dir=str(tmp_path / "c"),
                                    semiogenesis=sem, ontogenesis=ont,
                                    max_ticks=2)
    cog.run_bounded()
    return rt, ont, sem, cog


def test_metabolism_pressure_affects_perspective(tmp_path):
    rt, ont, sem, cog = _stack(tmp_path)
    sb = SelfBoundaryRuntime(
        state_dir=str(tmp_path / "sb"), sensorium=rt, ontogenesis=ont,
        semiogenesis=sem, cognition=cog,
        metabolism={"overload_state": True,
                    "dominant_perceptual_need": "quiet_need"}, max_ticks=1)
    sb.update(tick=0)
    # The metabolic overload becomes the perspective's uncertainty focus.
    assert sb.perspective.frame.uncertainty_focus == "overload"
    assert sb.perspective.frame.attention_focus == "quiet_need"


def test_concepts_signs_cognition_classified(tmp_path):
    rt, ont, sem, cog = _stack(tmp_path)
    sb = SelfBoundaryRuntime(state_dir=str(tmp_path / "sb"), sensorium=rt,
                             ontogenesis=ont, semiogenesis=sem, cognition=cog,
                             max_ticks=1)
    sb.update(tick=0)
    origins = {c.origin for c in sb.classifier.classifications}
    assert "perceptual_ontogenesis" in origins
    assert "semiogenesis" in origins


def test_simulations_validated_as_non_observation(tmp_path):
    rt, ont, sem, cog = _stack(tmp_path)
    # Ensure cognition produced at least one simulation.
    sb = SelfBoundaryRuntime(state_dir=str(tmp_path / "sb"), sensorium=rt,
                             ontogenesis=ont, semiogenesis=sem, cognition=cog,
                             max_ticks=1)
    sb.update(tick=0)
    sim_events = [e for e in sb.boundary.events
                  if e.zone == BoundaryZone.SIMULATION]
    # Simulations are placed on the simulation (non-observation) side.
    assert sb.sim_boundary.integrity() == 1.0
    if cog.simulations:
        assert sim_events
