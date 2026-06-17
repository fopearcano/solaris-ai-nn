"""Live cognition <- semiogenesis: consumes signs; missing/contaminated handled."""

from __future__ import annotations

import json
import os
import shutil

from solaris_ai_nn.live_birth import approved_governance, feeder_registry_template
from solaris_ai_nn.live_observation import PostBirthLiveObservationRuntime
from solaris_ai_nn.live_ontogenesis import FirstLiveOntogenesisRuntime
from solaris_ai_nn.live_semiogenesis import FirstLiveSemiogenesisRuntime
from solaris_ai_nn.live_cognition import (
    FirstLiveCognitionRuntime,
    SignInputLoader,
)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ONTO_FIXTURE = os.path.join(_ROOT, "examples", "live_ontogenesis",
                             "sample_stable_patterns.jsonl")


def _base(state, *, chain=True):
    for sub in ("governance", "feeders", "inbox", "certificates"):
        os.makedirs(os.path.join(state, sub), exist_ok=True)
    json.dump(approved_governance(), open(os.path.join(
        state, "governance", "LIVE_READONLY_GOVERNANCE.json"), "w"))
    json.dump(feeder_registry_template(), open(os.path.join(
        state, "feeders", "FEEDER_REGISTRY.json"), "w"))
    open(os.path.join(state, "certificates", "c.md"), "w").write("# c\n")
    shutil.copy(_ONTO_FIXTURE, os.path.join(state, "inbox", "ev.jsonl"))
    if chain:
        PostBirthLiveObservationRuntime(state_dir=state).run()
        FirstLiveOntogenesisRuntime(state_dir=state,
                                    allow_limited_birth=True).run()
        FirstLiveSemiogenesisRuntime(state_dir=state,
                                     allow_limited_birth=True).run()


def test_consumes_sign_memory(tmp_path):
    state = str(tmp_path)
    _base(state)
    rt = FirstLiveCognitionRuntime(
        state_dir=state, require_live_signs=True,
        profile="live_cognition_anticipation_limited_v0")
    rt.run()
    assert rt.cognition_status()["live_eligible_sign_count"] >= 1


def test_missing_sign_memory_blocks(tmp_path):
    state = str(tmp_path)
    _base(state, chain=False)  # no semiogenesis -> no sign memory
    rt = FirstLiveCognitionRuntime(state_dir=state, require_live_signs=True)
    res = rt.run()
    assert res["blocked"] is True
    assert any("sign" in b for b in res["blockers"])


def test_high_sign_contamination_blocks_promotion(tmp_path):
    recs = [{"sign_id": "s1", "private_token": "sig_live_op", "status": "born",
             "linked_concept_ids": ["c_op"], "utility_score": 0.6,
             "source_distribution": {"operator_pulse": 5},
             "supporting_refs": ["c_op"], "contradicting_refs": [],
             "contamination_findings": ["operator_pulse_dominance"]}]
    signs = SignInputLoader().from_records(recs, synthetic=True)
    rt = FirstLiveCognitionRuntime(
        state_dir=str(tmp_path),
        profile="live_cognition_anticipation_limited_v0")
    rt.analyze_signs(signs.signs)
    assert rt.cognition_status()["live_useful_trace_count"] == 0
