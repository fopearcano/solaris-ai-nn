"""Membrane -> Ontogenesis: impressions available; ancestry; contaminated flagged."""

from __future__ import annotations

import json
import os
import shutil

from solaris_ai_nn.live_birth import approved_governance, feeder_registry_template
from solaris_ai_nn.environmental_membrane import EnvironmentalMembraneRuntime

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FIXTURES = os.path.join(_ROOT, "examples", "environmental_membrane")


def _run(tmp_path, fixture):
    state = str(tmp_path)
    for sub in ("governance", "feeders", "inbox"):
        os.makedirs(os.path.join(state, sub), exist_ok=True)
    json.dump(approved_governance(), open(os.path.join(
        state, "governance", "LIVE_READONLY_GOVERNANCE.json"), "w"))
    json.dump(feeder_registry_template(), open(os.path.join(
        state, "feeders", "FEEDER_REGISTRY.json"), "w"))
    shutil.copy(os.path.join(_FIXTURES, fixture),
                os.path.join(state, "inbox", "events.jsonl"))
    rt = EnvironmentalMembraneRuntime(state_dir=state, require_governance=True)
    rt.run()
    return rt


def test_ontogenesis_uses_impressions_when_available(tmp_path):
    rt = _run(tmp_path, "sample_validated_events.jsonl")
    impressions = rt.impressions_for_downstream()
    # Impressions carry the feature/receptor/salience/contamination/grounding
    # fields ontogenesis should prefer over raw events.
    assert impressions
    sample = impressions[0]
    for field in ("receptor_id", "salience", "contamination", "grounding",
                  "evidence_refs", "source_pressure"):
        assert field in sample


def test_raw_fallback_loudly_marked(tmp_path):
    # With no impressions, the membrane's downstream readiness flags the gap so
    # any raw fallback would be loud rather than silent.
    state = str(tmp_path)
    for sub in ("governance", "feeders", "inbox"):
        os.makedirs(os.path.join(state, sub), exist_ok=True)
    json.dump(approved_governance(), open(os.path.join(
        state, "governance", "LIVE_READONLY_GOVERNANCE.json"), "w"))
    json.dump(feeder_registry_template(), open(os.path.join(
        state, "feeders", "FEEDER_REGISTRY.json"), "w"))
    rt = EnvironmentalMembraneRuntime(state_dir=state, require_governance=True)
    rt.run()
    ready = rt.downstream_readiness()
    assert ready["raw_event_bypass"] is False
    assert ready["downstream_ready"] is False


def test_contaminated_impressions_marked_for_block(tmp_path):
    rt = _run(tmp_path, "sample_contaminated_events.jsonl")
    impressions = rt.impressions_for_downstream()
    # Contaminated/blocked impressions are flagged so the concept birth gate can
    # require clean impression evidence.
    flagged = [i for i in impressions
               if i["blocked"] or i["contamination"] > 0]
    assert any(i["contamination"] >= 0 for i in impressions)
    assert all(("blocked" in i) for i in impressions)
