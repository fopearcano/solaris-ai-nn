"""Live semiogenesis Inner MAP + Evaluation integration."""

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


def test_inner_map_observer_attaches_semiogenesis(tmp_path):
    from solaris_ai_nn.inner_map.observer import InnerMapObserver
    from solaris_ai_nn.live_semiogenesis import FirstLiveSemiogenesisRuntime

    state = _setup(tmp_path)
    rt = FirstLiveSemiogenesisRuntime(state_dir=state, allow_limited_birth=True)
    rt.run()
    model = InnerMapObserver(live_semiogenesis=rt).update()
    assert model.live_semiogenesis is not None
    assert model.live_semiogenesis["live_semiogenesis_enabled"] is True


def test_inner_map_warning_when_unavailable():
    from solaris_ai_nn.inner_map.observer import InnerMapObserver

    model = InnerMapObserver().update()
    assert model.live_semiogenesis is None


def test_evaluation_metrics_computed(tmp_path):
    from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
    from solaris_ai_nn.evaluation.protocols import PROTOCOLS

    reg = ExperimentRegistry()
    m = reg.build_manifest("live_semiogenesis",
                           {"state_dir": str(tmp_path / "eval")})
    assert m.enabled_features.get("live_semiogenesis") is True
    res = PROTOCOLS["live_semiogenesis"](m)
    ls = res.metrics["live_semiogenesis"]
    assert ls["present"] is True
    assert ls["enables_cognition"] is False
    assert ls["signs_are_language_understanding"] is False


def test_evaluation_metrics_empty():
    from solaris_ai_nn.evaluation.metrics import live_semiogenesis_metrics

    assert live_semiogenesis_metrics(None) == {"present": False}


def test_alpha_orchestrator_reads_semiogenesis(tmp_path):
    from solaris_ai_nn.alpha_system.alpha_orchestrator import (
        AlphaResearchOrchestrator,
    )
    from solaris_ai_nn.live_semiogenesis import FirstLiveSemiogenesisRuntime

    state = _setup(tmp_path)
    FirstLiveSemiogenesisRuntime(state_dir=state, allow_limited_birth=True).run()
    o = AlphaResearchOrchestrator(state_dir=str(tmp_path / "alpha"))
    status = o.live_semiogenesis_status(live_state_dir=state)
    assert status["live_semiogenesis_enabled"] is True
    assert status["enables_cognition"] is False
    assert status["signs_are_language_understanding"] is False
