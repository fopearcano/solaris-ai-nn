"""Live observation integration: CLI, evaluation, Inner MAP, Alpha system."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.live_birth import approved_governance, feeder_registry_template


def _ev(eid, ts, sid):
    return {"event_id": eid, "timestamp_utc": ts, "source_id": sid,
            "modality": "scalar", "channel": "c", "read_only": True,
            "is_command": False, "human_label_is_ground_truth": False,
            "payload": {"v": 1},
            "quality": {"completeness": 1.0, "noise": 0.0, "is_absence": False,
                        "is_noisy": False},
            "safety": {"private_data": False, "contains_instruction": False,
                       "contains_secret": False, "allow_learning": False}}


def _setup(tmp_path):
    state = str(tmp_path)
    for sub in ("governance", "feeders", "inbox", "certificates"):
        os.makedirs(os.path.join(state, sub), exist_ok=True)
    json.dump(approved_governance(), open(os.path.join(
        state, "governance", "LIVE_READONLY_GOVERNANCE.json"), "w"))
    json.dump(feeder_registry_template(), open(os.path.join(
        state, "feeders", "FEEDER_REGISTRY.json"), "w"))
    open(os.path.join(state, "certificates", "BIRTH_CERTIFICATE_t.md"),
         "w").write("# cert\n")
    with open(os.path.join(state, "inbox", "e.jsonl"), "w") as fh:
        for i, sid in enumerate(["chronos_absence", "machine_body",
                                 "operator_pulse", "project_artifact_field"]):
            fh.write(json.dumps(_ev(f"e{i}", f"2026-06-17T08:0{i}:00Z",
                                    sid)) + "\n")
    return state


def test_cli_live_observe(tmp_path, capsys):
    from solaris_ai_nn.cli import main

    state = _setup(tmp_path)
    rc = main(["live-observe", "--state-dir", state])
    out = capsys.readouterr().out
    assert rc == 0
    assert "post-birth live observation" in out
    assert "stability status" in out


def test_cli_subcommands(tmp_path, capsys):
    from solaris_ai_nn.cli import main

    state = _setup(tmp_path)
    for cmd in ("live-source-health", "live-source-diet",
                "live-metabolism-calibration", "live-stability-gate"):
        rc = main([cmd, "--state-dir", state])
        assert rc == 0, cmd


def test_evaluation_protocol_and_metrics(tmp_path):
    from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
    from solaris_ai_nn.evaluation.protocols import PROTOCOLS

    reg = ExperimentRegistry()
    m = reg.build_manifest("live_observation",
                           {"state_dir": str(tmp_path / "eval")})
    assert m.enabled_features.get("live_observation") is True
    res = PROTOCOLS["live_observation"](m)
    lo = res.metrics["live_observation"]
    assert lo["present"] is True
    assert lo["learns"] is False
    assert lo["live_source_count"] >= 1


def test_evaluation_safety_protocol():
    from solaris_ai_nn.evaluation.protocols import PROTOCOLS
    from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry

    reg = ExperimentRegistry()
    m = reg.build_manifest("live_observation_safety", {})
    res = PROTOCOLS["live_observation_safety"](m)
    lo = res.metrics["live_observation"]
    assert lo["feeder_control_blocked"] is True
    assert lo["default_learning_blocked"] is True
    assert lo["can_enable_learning_by_default"] is False


def test_metrics_empty():
    from solaris_ai_nn.evaluation.metrics import live_observation_metrics

    assert live_observation_metrics(None) == {"present": False}


def test_inner_map_observer_attaches_observation(tmp_path):
    from solaris_ai_nn.inner_map.observer import InnerMapObserver
    from solaris_ai_nn.live_observation import PostBirthLiveObservationRuntime

    state = _setup(tmp_path)
    rt = PostBirthLiveObservationRuntime(state_dir=state)
    rt.run()
    obs = InnerMapObserver(live_observation=rt)
    model = obs.update()
    assert model.live_observation is not None
    assert model.live_observation["live_observation_enabled"] is True


def test_alpha_orchestrator_reads_observation(tmp_path):
    from solaris_ai_nn.alpha_system.alpha_orchestrator import (
        AlphaResearchOrchestrator,
    )
    from solaris_ai_nn.live_observation import PostBirthLiveObservationRuntime

    state = _setup(tmp_path)
    rt = PostBirthLiveObservationRuntime(state_dir=state)
    rt.run()
    o = AlphaResearchOrchestrator(state_dir=str(tmp_path / "alpha"))
    status = o.live_observation_status(live_state_dir=state)
    assert status["live_observation_enabled"] is True
    assert status["learns"] is False
    assert status["controls_feeders"] is False


def test_state_graph_has_observation_nodes():
    from solaris_ai_nn.inner_map.state_graph import build_default_state_graph

    g = build_default_state_graph()
    blob = str(g.to_dict() if hasattr(g, "to_dict") else g.__dict__)
    assert "PostBirthLiveObservationRuntime" in blob
    assert "LiveStabilityGate" in blob
