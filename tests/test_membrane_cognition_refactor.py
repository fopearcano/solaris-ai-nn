"""Live Cognition refactor: trace records carry ancestry; event vs impression."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.live_cognition.cognition_memory import LiveCognitionRecord
from solaris_ai_nn.membrane_integration import (
    LiveCognitionMembraneAdapter,
    MembraneAncestryBuilder,
    SensoryImpressionLoader,
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _membrane_integration_helpers import load_fixture, stage_pipeline  # noqa: E402


def test_cognition_record_has_ancestry_refs():
    rec = LiveCognitionRecord(trace_id="t1", kind="prediction", status="useful",
                              ancestry_refs=["imp_b1", "s_machine"])
    d = rec.to_dict()
    assert d["ancestry_refs"] == ["imp_b1", "s_machine"]
    assert d["implies_reasoning"] is False


def test_trace_ancestry_distinguishes_event_vs_impression(tmp_path):
    state = stage_pipeline(str(tmp_path))
    load = SensoryImpressionLoader().load(state)
    anc = MembraneAncestryBuilder().build(
        impressions=load.impressions,
        concept_records=load_fixture("proto_concept.json")["records"],
        sign_records=load_fixture("sign_record.json")["records"],
        cognition_records=load_fixture("cognition_trace.json")["records"],
        membrane_available=True)
    r = LiveCognitionMembraneAdapter().run(state, anc)
    assert r.data["traces_with_impression_ancestry"] >= 1
    assert r.data["distinguishes_event_vs_impression_prediction"] is True
    trace = next(c for c in anc.chains if c.artifact_type == "cognition_trace")
    assert trace.has_impression_ancestry is True
    assert trace.impression_ids
