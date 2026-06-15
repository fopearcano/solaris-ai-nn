"""Plural sensorium <-> developmental milestones / research comparisons."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.plural_sensorium.sensorium_runtime import SensoriumMilestone


def _runtime(tmp_path, modalities):
    os.makedirs(str(tmp_path), exist_ok=True)
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path) + "/s")
    for mod in modalities:
        path = os.path.join(tmp_path, f"{mod}.jsonl")
        with open(path, "w") as fh:
            for i in range(8):
                fh.write(json.dumps({"modality": mod, "v": 0.6,
                                     "ts": float(i)}) + "\n")
        rt.add_feeder(fixture_feeder(f"{mod}_feed", path, mod))
    rt.run_bounded(max_polls=1)
    return rt


def test_developmental_milestones_recorded(tmp_path):
    rt = _runtime(str(tmp_path), ["human_textual", "alien_rf"])
    assert SensoriumMilestone.FIRST_SENSORIUM_EVENT in rt.milestones
    assert SensoriumMilestone.FIRST_HUMAN_LIKE_MODALITY_EVENT in rt.milestones
    assert SensoriumMilestone.FIRST_NON_HUMAN_MODALITY_EVENT in rt.milestones
    assert SensoriumMilestone.FIRST_RF_PATTERN in rt.milestones


def test_research_comparison_runs(tmp_path):
    # human-like-only vs non-human-only vs mixed produce (possibly different)
    # internal structures -- the research protocols all run and return results.
    reg = ExperimentRegistry()
    for name in ("human_like_sensorium", "non_human_sensorium",
                 "mixed_sensorium"):
        manifest = reg.build_manifest(name, {"steps": 6,
                                             "state_dir": str(tmp_path / name)})
        result = PROTOCOLS[name](manifest)
        assert result.success
        assert "sensorium" in result.metrics


def test_human_vs_nonhuman_can_differ(tmp_path):
    human = _runtime(tmp_path / "h", ["human_textual"])
    nonhuman = _runtime(tmp_path / "n", ["alien_rf", "alien_echo"])
    # Different sensoria yield different active-modality structure.
    assert (human.plural_sensorium_status()["active_modality_count"]
            != nonhuman.plural_sensorium_status()["active_modality_count"])
