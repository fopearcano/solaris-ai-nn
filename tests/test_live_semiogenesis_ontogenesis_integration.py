"""Live semiogenesis <- ontogenesis: consumes concepts; missing/contaminated block."""

from __future__ import annotations

import json
import os
import shutil

from solaris_ai_nn.live_birth import approved_governance, feeder_registry_template
from solaris_ai_nn.live_observation import PostBirthLiveObservationRuntime
from solaris_ai_nn.live_ontogenesis import FirstLiveOntogenesisRuntime
from solaris_ai_nn.live_semiogenesis import (
    ConceptInputLoader,
    FirstLiveSemiogenesisRuntime,
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


def test_consumes_concept_memory(tmp_path):
    state = str(tmp_path)
    _base(state)
    rt = FirstLiveSemiogenesisRuntime(state_dir=state,
                                      require_live_concepts=True,
                                      allow_limited_birth=True)
    rt.run()
    assert rt.semiogenesis_status()["live_eligible_concept_count"] >= 1


def test_missing_concept_memory_blocks(tmp_path):
    state = str(tmp_path)
    _base(state, chain=False)  # no observation/ontogenesis -> no concept memory
    rt = FirstLiveSemiogenesisRuntime(state_dir=state,
                                      require_live_concepts=True)
    res = rt.run()
    assert res["blocked"] is True
    assert any("concept" in b for b in res["blockers"])


def test_high_concept_contamination_blocks_sign_birth(tmp_path):
    # All concepts contaminated -> none eligible -> sign birth blocked.
    recs = [{"concept_id": "c1", "feature_signature": "operator_pulse:pulse:zz",
             "status": "born", "stability_score": 0.6, "recurrence_count": 5,
             "source_distribution": {"operator_pulse": 5},
             "modality_distribution": {"pulse": 5},
             "supporting_event_ids": ["e1"],
             "contamination_findings": ["operator_pulse_dominance"]}]
    ci = ConceptInputLoader().from_records(recs, synthetic=True)
    rt = FirstLiveSemiogenesisRuntime(state_dir=str(tmp_path),
                                      allow_limited_birth=True)
    # Pass the contaminated concept directly; it must not yield a born sign.
    rt.analyze_concepts(ci.concepts)
    assert rt.semiogenesis_status()["live_born_sign_count"] == 0
