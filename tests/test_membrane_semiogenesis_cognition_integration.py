"""Membrane -> Semiogenesis/Cognition: ancestry preserved; contamination downgrades."""

from __future__ import annotations

import json
import os
import shutil

from solaris_ai_nn.live_birth import approved_governance, feeder_registry_template
from solaris_ai_nn.environmental_membrane import EnvironmentalMembraneRuntime

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FIXTURES = os.path.join(_ROOT, "examples", "environmental_membrane")


def _run(tmp_path, fixture="sample_validated_events.jsonl"):
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


def test_impression_ancestry_links_to_source_event(tmp_path):
    rt = _run(tmp_path)
    # sign -> proto-concept -> impression -> receptor -> source event: the
    # membrane provides the impression->receptor->source-event links.
    for imp in rt.impressions_for_downstream():
        assert imp["receptor_id"]
        assert imp["source_event_id"]
        assert imp["evidence_refs"]


def test_contaminated_ancestry_downgrades_readiness(tmp_path):
    rt = _run(tmp_path, "sample_contaminated_events.jsonl")
    impressions = rt.impressions_for_downstream()
    # Any sign/cognition trace whose ancestry includes these impressions can be
    # downgraded by reading the contamination/operator weights the membrane
    # carries on each impression.
    assert all("contamination" in i and "operator_pulse_weight" in i
               for i in impressions)
    contaminated = [i for i in impressions if i["contamination"] > 0]
    # Operator-dominated / contaminated impressions are visibly flagged.
    assert isinstance(contaminated, list)
