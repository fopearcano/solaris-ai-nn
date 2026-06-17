"""Live Semiogenesis refactor: sign records carry impression ancestry refs."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.live_semiogenesis.sign_memory import LiveSignRecord
from solaris_ai_nn.membrane_integration import (
    LiveSemiogenesisMembraneAdapter,
    MembraneAncestryBuilder,
    SensoryImpressionLoader,
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _membrane_integration_helpers import load_fixture, stage_pipeline  # noqa: E402


def test_sign_record_has_ancestry_refs():
    rec = LiveSignRecord(sign_id="s1", private_token="t", status="born",
                         ancestry_refs=["imp_b1", "rcpt_1"])
    d = rec.to_dict()
    assert "ancestry_refs" in d
    assert d["ancestry_refs"] == ["imp_b1", "rcpt_1"]
    assert d["implies_language_understanding"] is False


def test_sign_ancestry_to_impressions(tmp_path):
    state = stage_pipeline(str(tmp_path))
    load = SensoryImpressionLoader().load(state)
    anc = MembraneAncestryBuilder().build(
        impressions=load.impressions,
        concept_records=load_fixture("proto_concept.json")["records"],
        sign_records=load_fixture("sign_record.json")["records"],
        cognition_records=load_fixture("cognition_trace.json")["records"],
        membrane_available=True)
    r = LiveSemiogenesisMembraneAdapter().run(state, anc)
    assert r.data["signs_with_impression_ancestry"] >= 1
    assert r.data["contaminated_ancestry_blocks_birth"] is True


def test_sign_missing_ancestry_strict_blocks(tmp_path):
    state = stage_pipeline(str(tmp_path), include_bypass=True)
    load = SensoryImpressionLoader().load(state)
    anc = MembraneAncestryBuilder().build(
        impressions=load.impressions,
        concept_records=load_fixture("bypass_concept.json")["records"],
        sign_records=load_fixture("sign_record.json")["records"],
        cognition_records=load_fixture("cognition_trace.json")["records"],
        membrane_available=True)
    r = LiveSemiogenesisMembraneAdapter().run(state, anc, strict=True)
    assert r.status == "blocked"
