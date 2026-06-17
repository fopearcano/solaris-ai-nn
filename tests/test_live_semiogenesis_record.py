"""Live semiogenesis record: generated, disclaimer present, blockers visible."""

from __future__ import annotations

import json
import os
import shutil

from solaris_ai_nn.live_birth import approved_governance, feeder_registry_template
from solaris_ai_nn.live_observation import PostBirthLiveObservationRuntime
from solaris_ai_nn.live_ontogenesis import FirstLiveOntogenesisRuntime
from solaris_ai_nn.live_semiogenesis import FirstLiveSemiogenesisRuntime

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ONTO_FIXTURE = os.path.join(_ROOT, "examples", "live_ontogenesis",
                             "sample_stable_patterns.jsonl")


def _setup(tmp_path):
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
    return state


def test_record_generated(tmp_path):
    state = _setup(tmp_path)
    FirstLiveSemiogenesisRuntime(state_dir=state, allow_limited_birth=True).run()
    reports = os.path.join(state, "semiogenesis", "reports")
    md = [f for f in os.listdir(reports)
          if f.startswith("LIVE_SEMIOGENESIS_RECORD_") and f.endswith(".md")]
    assert md


def test_disclaimer_present(tmp_path):
    state = _setup(tmp_path)
    FirstLiveSemiogenesisRuntime(state_dir=state, allow_limited_birth=True).run()
    reports = os.path.join(state, "semiogenesis", "reports")
    md = [f for f in os.listdir(reports)
          if f.startswith("LIVE_SEMIOGENESIS_RECORD_") and f.endswith(".md")][0]
    text = open(os.path.join(reports, md)).read().lower()
    assert "operational internal reference structures" in text
    assert "do not imply language understanding" in text


def test_blockers_visible(tmp_path):
    state = str(tmp_path)
    for sub in ("governance", "feeders", "inbox", "certificates"):
        os.makedirs(os.path.join(state, sub), exist_ok=True)
    json.dump(approved_governance(), open(os.path.join(
        state, "governance", "LIVE_READONLY_GOVERNANCE.json"), "w"))
    json.dump(feeder_registry_template(), open(os.path.join(
        state, "feeders", "FEEDER_REGISTRY.json"), "w"))
    rt = FirstLiveSemiogenesisRuntime(state_dir=state,
                                      require_birth_certificate=True,
                                      require_observation_stability=True,
                                      require_live_concepts=True)
    result = rt.run()
    assert result["blocked"] is True
    assert result["blockers"]
