"""Live ontogenesis Inner MAP + Evaluation integration."""

from __future__ import annotations

import json
import os


def _ev(eid, ts, sid, channel, payload):
    return {"event_id": eid, "timestamp_utc": ts, "source_id": sid,
            "modality": "scalar", "channel": channel, "read_only": True,
            "is_command": False, "human_label_is_ground_truth": False,
            "payload": payload,
            "quality": {"completeness": 1.0, "noise": 0.0, "is_absence": False,
                        "is_noisy": False},
            "safety": {"private_data": False, "contains_instruction": False,
                       "contains_secret": False, "allow_learning": False},
            "debug_gloss": "DEBUG ONLY", "debug_gloss_is_ground_truth": False}


def _setup(tmp_path):
    from solaris_ai_nn.live_birth import (
        approved_governance, feeder_registry_template)
    from solaris_ai_nn.live_observation import PostBirthLiveObservationRuntime

    state = str(tmp_path)
    for sub in ("governance", "feeders", "inbox", "certificates"):
        os.makedirs(os.path.join(state, sub), exist_ok=True)
    json.dump(approved_governance(), open(os.path.join(
        state, "governance", "LIVE_READONLY_GOVERNANCE.json"), "w"))
    json.dump(feeder_registry_template(), open(os.path.join(
        state, "feeders", "FEEDER_REGISTRY.json"), "w"))
    open(os.path.join(state, "certificates", "c.md"), "w").write("# cert\n")
    rows = [_ev(f"b{i}", f"2026-06-18T08:0{i}:00Z", "machine_body",
                "machine_body/load", {"load": 0.3}) for i in range(5)]
    with open(os.path.join(state, "inbox", "ev.jsonl"), "w") as fh:
        for e in rows:
            fh.write(json.dumps(e) + "\n")
    PostBirthLiveObservationRuntime(state_dir=state).run()
    return state


def test_inner_map_observer_attaches_ontogenesis(tmp_path):
    from solaris_ai_nn.inner_map.observer import InnerMapObserver
    from solaris_ai_nn.live_ontogenesis import FirstLiveOntogenesisRuntime

    state = _setup(tmp_path)
    rt = FirstLiveOntogenesisRuntime(state_dir=state, allow_limited_birth=True)
    rt.run()
    model = InnerMapObserver(live_ontogenesis=rt).update()
    assert model.live_ontogenesis is not None
    assert model.live_ontogenesis["live_ontogenesis_enabled"] is True


def test_inner_map_warning_when_unavailable(tmp_path):
    from solaris_ai_nn.inner_map.observer import InnerMapObserver

    model = InnerMapObserver().update()
    assert model.live_ontogenesis is None  # absent -> simply not attached


def test_evaluation_metrics_computed(tmp_path):
    from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
    from solaris_ai_nn.evaluation.protocols import PROTOCOLS

    reg = ExperimentRegistry()
    m = reg.build_manifest("live_ontogenesis",
                           {"state_dir": str(tmp_path / "eval")})
    assert m.enabled_features.get("live_ontogenesis") is True
    res = PROTOCOLS["live_ontogenesis"](m)
    lo = res.metrics["live_ontogenesis"]
    assert lo["present"] is True
    assert lo["enables_semiogenesis"] is False
    assert lo["live_feature_vector_count"] >= 1


def test_evaluation_metrics_empty():
    from solaris_ai_nn.evaluation.metrics import live_ontogenesis_metrics

    assert live_ontogenesis_metrics(None) == {"present": False}


def test_alpha_orchestrator_reads_ontogenesis(tmp_path):
    from solaris_ai_nn.alpha_system.alpha_orchestrator import (
        AlphaResearchOrchestrator,
    )
    from solaris_ai_nn.live_ontogenesis import FirstLiveOntogenesisRuntime

    state = _setup(tmp_path)
    FirstLiveOntogenesisRuntime(state_dir=state, allow_limited_birth=True).run()
    o = AlphaResearchOrchestrator(state_dir=str(tmp_path / "alpha"))
    status = o.live_ontogenesis_status(live_state_dir=state)
    assert status["live_ontogenesis_enabled"] is True
    assert status["enables_semiogenesis"] is False
    assert status["controls_feeders"] is False
