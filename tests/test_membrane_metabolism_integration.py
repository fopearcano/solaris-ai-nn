"""Membrane -> Perceptual Metabolism: nutrient handoff; no data request/control."""

from __future__ import annotations

import json
import os
import shutil

from solaris_ai_nn.live_birth import approved_governance, feeder_registry_template
from solaris_ai_nn.environmental_membrane import EnvironmentalMembraneRuntime

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FIXTURES = os.path.join(_ROOT, "examples", "environmental_membrane")


def _run(tmp_path):
    state = str(tmp_path)
    for sub in ("governance", "feeders", "inbox"):
        os.makedirs(os.path.join(state, sub), exist_ok=True)
    json.dump(approved_governance(), open(os.path.join(
        state, "governance", "LIVE_READONLY_GOVERNANCE.json"), "w"))
    json.dump(feeder_registry_template(), open(os.path.join(
        state, "feeders", "FEEDER_REGISTRY.json"), "w"))
    shutil.copy(os.path.join(_FIXTURES, "sample_validated_events.jsonl"),
                os.path.join(state, "inbox", "events.jsonl"))
    rt = EnvironmentalMembraneRuntime(state_dir=state, require_governance=True)
    rt.run()
    return rt


def test_metabolism_consumes_impression_nutrients(tmp_path):
    rt = _run(tmp_path)
    nutrients = rt.metabolism_nutrients()
    assert nutrients["nutrient_impression_count"] >= 1
    for field in ("mean_intensity", "mean_salience", "mean_novelty",
                  "mean_repetition", "mean_contamination",
                  "source_pressure_status"):
        assert field in nutrients


def test_no_source_request_or_control(tmp_path):
    rt = _run(tmp_path)
    nutrients = rt.metabolism_nutrients()
    assert nutrients["requests_more_data"] is False
    assert nutrients["alters_feeder_behavior"] is False
