"""Cognition consumes signs and proto-concepts and creates cognitive moves."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.perceptual_ontogenesis import PerceptualOntogenesisRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.semiogenesis import SemiogenesisRuntime
from solaris_ai_nn.sensorium_cognition import SensoriumCognitionRuntime


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
    return sem, ont


def test_consumes_signs(tmp_path):
    sem, ont = _stack(tmp_path)
    cog = SensoriumCognitionRuntime(state_dir=str(tmp_path / "c"),
                                    semiogenesis=sem, ontogenesis=ont,
                                    max_ticks=2)
    cog.update(tick=0)
    assert cog._signs()  # signs were read from semiogenesis
    assert cog._patterns() is not None


def test_consumes_proto_concepts(tmp_path):
    sem, ont = _stack(tmp_path)
    cog = SensoriumCognitionRuntime(state_dir=str(tmp_path / "c"),
                                    semiogenesis=sem, ontogenesis=ont,
                                    max_ticks=2)
    cog.update(tick=0)
    assert cog._concepts()  # concepts were read from ontogenesis


def test_creates_cognitive_moves(tmp_path):
    sem, ont = _stack(tmp_path)
    cog = SensoriumCognitionRuntime(state_dir=str(tmp_path / "c"),
                                    semiogenesis=sem, ontogenesis=ont,
                                    max_ticks=2)
    cog.run_bounded()
    assert cog.moves
    # Moves reference internal signs (not human words).
    assert any(m.input_sign_refs for m in cog.moves)


def test_consumes_bare_sign_list(tmp_path):
    sem, ont = _stack(tmp_path)
    signs = list(sem.signs.values())
    cog = SensoriumCognitionRuntime(state_dir=str(tmp_path / "c2"),
                                    semiogenesis=signs, max_ticks=1)
    cog.update(tick=0)
    assert len(cog._signs()) == len(signs)
