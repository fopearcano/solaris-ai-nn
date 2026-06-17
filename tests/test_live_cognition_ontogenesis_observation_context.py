"""Live cognition uses observation/ontogenesis context; writes no thresholds."""

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
    FirstLiveSemiogenesisRuntime(state_dir=state, allow_limited_birth=True).run()
    return state


def test_uses_source_diet_and_load_context(tmp_path):
    state = _setup(tmp_path)
    rt = FirstLiveCognitionRuntime(
        state_dir=state,
        profile="live_cognition_anticipation_limited_v0")
    rt.run()
    assert rt.observation["present"] is True
    assert "source_diet" in rt.observation
    assert "load" in rt.observation


def test_does_not_write_thresholds(tmp_path):
    state = _setup(tmp_path)
    metab_dir = os.path.join(state, "observation", "metabolism")
    before = sorted(os.listdir(metab_dir)) if os.path.isdir(metab_dir) else []
    FirstLiveCognitionRuntime(
        state_dir=state,
        profile="live_cognition_anticipation_limited_v0").run()
    after = sorted(os.listdir(metab_dir)) if os.path.isdir(metab_dir) else []
    assert before == after
