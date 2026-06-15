"""SourceDietAnalyzer: human-like dominance; non-human dominance; diversity."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.perceptual_metabolism import SourceDietAnalyzer
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder


def _sensorium(tmp_path, name, modalities, labelled=False):
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / name))
    feeds = tmp_path / name
    feeds.mkdir(parents=True, exist_ok=True)
    for mod in modalities:
        path = os.path.join(str(feeds), f"{mod}.jsonl")
        with open(path, "w") as fh:
            for i in range(8):
                rec = {"modality": mod, "v": 0.6, "ts": float(i)}
                if labelled and mod == "human_textual":
                    rec["annotation"] = f"obs {i}"
                    rec["annotation_status"] = "human_label_external"
                fh.write(json.dumps(rec) + "\n")
        rt.add_feeder(fixture_feeder(f"{mod}_feed", path, mod))
    rt.run_bounded(max_polls=1)
    return rt


def test_human_like_dominance_detected(tmp_path):
    rt = _sensorium(tmp_path, "h", ["human_textual"], labelled=True)
    diet = SourceDietAnalyzer().analyze(rt)
    assert diet.dominant_class == "human_like"
    assert diet.human_label_dominance > 0.0
    assert diet.modality_dominance == 1.0


def test_non_human_dominance_detected(tmp_path):
    rt = _sensorium(tmp_path, "n", ["alien_rf", "alien_echo", "vibration"])
    diet = SourceDietAnalyzer().analyze(rt)
    assert diet.dominant_class == "non_human"
    assert diet.non_human_contribution > 0.5


def test_mixed_diet_diversity_computed(tmp_path):
    rt = _sensorium(tmp_path, "m", ["human_textual", "alien_rf", "vibration"])
    diet = SourceDietAnalyzer().analyze(rt)
    assert diet.diet_diversity > 0.0
    assert 0.0 <= diet.modality_dominance <= 1.0


def test_dominance_measured_not_hidden(tmp_path):
    rt = _sensorium(tmp_path, "h2", ["human_textual"], labelled=True)
    data = SourceDietAnalyzer().analyze(rt).to_dict()
    assert "dominance is measured, never hidden" in data["note"]
