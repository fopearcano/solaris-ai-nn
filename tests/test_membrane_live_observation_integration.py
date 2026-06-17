"""Membrane <- Live Observation: observation reads impression reports; event vs impression."""

from __future__ import annotations

import json
import os
import shutil

from solaris_ai_nn.live_birth import approved_governance, feeder_registry_template
from solaris_ai_nn.environmental_membrane import EnvironmentalMembraneRuntime

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FIXTURES = os.path.join(_ROOT, "examples", "environmental_membrane")


def _run_membrane(tmp_path):
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
    return state, rt


def test_observation_can_consume_impression_reports(tmp_path):
    state, rt = _run_membrane(tmp_path)
    # The impression index + source-pressure report are available for observation.
    idx = os.path.join(state, "membrane", "impressions",
                       "SENSORY_IMPRESSION_INDEX.json")
    assert os.path.isfile(idx)
    data = json.load(open(idx))
    assert data["membrane_impression_count"] >= 1


def test_source_diet_distinguishes_event_and_impression_diet(tmp_path):
    state, rt = _run_membrane(tmp_path)
    st = rt.membrane_status()
    # Event input count and impression count are reported separately so an
    # observation layer can distinguish the raw-event diet from the impression
    # diet.
    assert "membrane_event_input_count" in st
    assert "membrane_impression_count" in st
    impressions = rt.impressions_for_downstream()
    assert all("impression_kind" in i for i in impressions)
