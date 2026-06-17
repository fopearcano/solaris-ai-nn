"""Live cognition Inner MAP + Evaluation integration."""

from __future__ import annotations

import json
import os
import shutil

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ONTO_FIXTURE = os.path.join(_ROOT, "examples", "live_ontogenesis",
                             "sample_stable_patterns.jsonl")


def _setup(tmp_path):
    from solaris_ai_nn.live_birth import (
        approved_governance, feeder_registry_template)
    from solaris_ai_nn.live_observation import PostBirthLiveObservationRuntime
    from solaris_ai_nn.live_ontogenesis import FirstLiveOntogenesisRuntime
    from solaris_ai_nn.live_semiogenesis import FirstLiveSemiogenesisRuntime

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


def test_inner_map_observer_attaches_cognition(tmp_path):
    from solaris_ai_nn.inner_map.observer import InnerMapObserver
    from solaris_ai_nn.live_cognition import FirstLiveCognitionRuntime

    state = _setup(tmp_path)
    rt = FirstLiveCognitionRuntime(
        state_dir=state, profile="live_cognition_anticipation_limited_v0")
    rt.run()
    model = InnerMapObserver(live_cognition=rt).update()
    assert model.live_cognition is not None
    assert model.live_cognition["live_cognition_enabled"] is True


def test_inner_map_warning_when_unavailable():
    from solaris_ai_nn.inner_map.observer import InnerMapObserver

    model = InnerMapObserver().update()
    assert model.live_cognition is None


def test_evaluation_metrics_computed(tmp_path):
    from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
    from solaris_ai_nn.evaluation.protocols import PROTOCOLS

    reg = ExperimentRegistry()
    m = reg.build_manifest("live_cognition",
                           {"state_dir": str(tmp_path / "eval")})
    assert m.enabled_features.get("live_cognition") is True
    res = PROTOCOLS["live_cognition"](m)
    lc = res.metrics["live_cognition"]
    assert lc["present"] is True
    assert lc["enables_action"] is False
    assert lc["traces_prove_reasoning"] is False


def test_evaluation_metrics_empty():
    from solaris_ai_nn.evaluation.metrics import live_cognition_metrics

    assert live_cognition_metrics(None) == {"present": False}


def test_alpha_orchestrator_reads_cognition(tmp_path):
    from solaris_ai_nn.alpha_system.alpha_orchestrator import (
        AlphaResearchOrchestrator,
    )
    from solaris_ai_nn.live_cognition import FirstLiveCognitionRuntime

    state = _setup(tmp_path)
    FirstLiveCognitionRuntime(
        state_dir=state,
        profile="live_cognition_anticipation_limited_v0").run()
    o = AlphaResearchOrchestrator(state_dir=str(tmp_path / "alpha"))
    status = o.live_cognition_status(live_state_dir=state)
    assert status["live_cognition_enabled"] is True
    assert status["enables_action"] is False
    assert status["traces_prove_reasoning"] is False
