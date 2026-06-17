"""Live cognition research/claims integration: evidence recorded, operational."""

from __future__ import annotations

import json
import os
import shutil

from solaris_ai_nn.live_birth import approved_governance, feeder_registry_template
from solaris_ai_nn.live_observation import PostBirthLiveObservationRuntime
from solaris_ai_nn.live_ontogenesis import FirstLiveOntogenesisRuntime
from solaris_ai_nn.live_semiogenesis import FirstLiveSemiogenesisRuntime
from solaris_ai_nn.live_cognition import FirstLiveCognitionRuntime

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ONTO_FIXTURE = os.path.join(_ROOT, "examples", "live_ontogenesis",
                             "sample_stable_patterns.jsonl")


def _run(tmp_path, profile):
    state = str(tmp_path)
    for sub in ("governance", "feeders", "inbox", "certificates"):
        os.makedirs(os.path.join(state, sub), exist_ok=True)
    json.dump(approved_governance(), open(os.path.join(
        state, "governance", "LIVE_READONLY_GOVERNANCE.json"), "w"))
    json.dump(feeder_registry_template(), open(os.path.join(
        state, "feeders", "FEEDER_REGISTRY.json"), "w"))
    open(os.path.join(state, "certificates", "c.md"), "w").write("# cert\n")
    shutil.copy(_ONTO_FIXTURE, os.path.join(state, "inbox", "ev.jsonl"))
    PostBirthLiveObservationRuntime(state_dir=state).run()
    FirstLiveOntogenesisRuntime(state_dir=state, allow_limited_birth=True).run()
    FirstLiveSemiogenesisRuntime(state_dir=state, allow_limited_birth=True).run()
    rt = FirstLiveCognitionRuntime(state_dir=state, profile=profile)
    rt.run()
    return rt


def test_research_cycle_evidence_recorded(tmp_path):
    rt = _run(tmp_path, "live_cognition_anticipation_limited_v0")
    update = rt.research_cycle_update()
    assert update["cognition_evidence_recorded"] is True
    assert update["next_action"] in (
        "Prepare live self-boundary tracking protocol",
        "Resolve cognition blockers",
        "Continue live cognition observation")
    assert update["operational_only"] is True


def test_claims_marked_operational_only(tmp_path):
    rt = _run(tmp_path, "live_cognition_anticipation_limited_v0")
    claims = rt.scientific_claims_update()
    assert claims["evidence_kind"] == \
        "operational_sign_based_anticipation_record"
    assert claims["blocks_reasoning_proof_interpretation"] is True
    assert claims["blocks_language_understanding_interpretation"] is True
    assert claims["blocks_consciousness_life_agency_interpretation"] is True


def test_trace_only_run_marked_inconclusive(tmp_path):
    rt = _run(tmp_path, "live_cognition_trace_v0")
    claims = rt.scientific_claims_update()
    assert claims["trace_only_run"] is True
    assert claims["inconclusive_for_consciousness"] is True
