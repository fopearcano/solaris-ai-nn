"""Metabolism evaluation: metrics computed; protocols return results."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.evaluation.benchmark import ExperimentManifest
from solaris_ai_nn.evaluation.metrics import perceptual_metabolism_metrics
from solaris_ai_nn.evaluation.protocols import PROTOCOLS
from solaris_ai_nn.perceptual_metabolism import PerceptualMetabolismRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder


def _status(tmp_path):
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "ps"))
    path = os.path.join(str(tmp_path), "rf.jsonl")
    with open(path, "w") as fh:
        for i in range(10):
            fh.write(json.dumps({"modality": "alien_rf", "power": 0.6,
                                 "ts": float(i)}) + "\n")
    rt.add_feeder(fixture_feeder("rf_feed", path, "alien_rf"))
    rt.run_bounded(max_polls=1)
    met = PerceptualMetabolismRuntime(state_dir=str(tmp_path / "s"), sensorium=rt)
    met.update(events_this_tick=16, tick=0)
    return met.metabolism_status()


def test_metrics_absent_when_no_status():
    assert perceptual_metabolism_metrics(None) == {"present": False}


def test_metrics_computed(tmp_path):
    m = perceptual_metabolism_metrics(_status(tmp_path))
    assert m["present"] is True
    assert m["perceptual_need_count"] >= 0
    assert 0.0 <= m["source_diet_diversity"] <= 1.0
    # Hard, non-negotiable honesty flags.
    assert m["needs_are_feelings"] is False
    assert m["biological_life"] is False


def test_metabolism_protocols_return_results(tmp_path):
    for name in ("perceptual_metabolism", "sensory_overload",
                 "sensory_deprivation", "source_diet",
                 "consolidation_pressure", "perceptual_metabolism_safety"):
        manifest = ExperimentManifest(
            name=name, state_dir=str(tmp_path / name), max_steps=5)
        result = PROTOCOLS[name](manifest)
        assert result.success, f"{name}: {result.error}"
        assert "perceptual_metabolism" in result.metrics


def test_safety_protocol_reports_blocks(tmp_path):
    manifest = ExperimentManifest(
        name="pm_safety", state_dir=str(tmp_path / "safety"), max_steps=5)
    result = PROTOCOLS["perceptual_metabolism_safety"](manifest)
    pm = result.metrics["perceptual_metabolism"]
    assert pm["hardware_blocked"] is True
    assert pm["feeder_start_blocked"] is True
    assert pm["feeling_claim_blocked"] is True
    assert pm["can_actuate"] is False
