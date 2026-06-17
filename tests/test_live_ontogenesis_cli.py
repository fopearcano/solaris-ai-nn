"""Live ontogenesis CLI: commands work; strict returns nonzero on blocker."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.cli import main
from solaris_ai_nn.live_birth import approved_governance, feeder_registry_template
from solaris_ai_nn.live_observation import PostBirthLiveObservationRuntime


def _ev(eid, ts, sid, channel, payload, modality="scalar", absence=False):
    return {"event_id": eid, "timestamp_utc": ts, "source_id": sid,
            "modality": modality, "channel": channel, "read_only": True,
            "is_command": False, "human_label_is_ground_truth": False,
            "payload": payload,
            "quality": {"completeness": 1.0, "noise": 0.0, "is_absence": absence,
                        "is_noisy": False},
            "safety": {"private_data": False, "contains_instruction": False,
                       "contains_secret": False, "allow_learning": False},
            "debug_gloss": "DEBUG ONLY", "debug_gloss_is_ground_truth": False}


def _setup(tmp_path, observation=True):
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
    rows += [_ev(f"w{i}", f"2026-06-18T08:1{i}:00Z",
                 "local_weather_readonly_external", "weather/t", {"t": 19})
             for i in range(4)]
    with open(os.path.join(state, "inbox", "ev.jsonl"), "w") as fh:
        for e in rows:
            fh.write(json.dumps(e) + "\n")
    if observation:
        PostBirthLiveObservationRuntime(state_dir=state).run()
    return state


def test_cli_live_ontogenesis(tmp_path, capsys):
    state = _setup(tmp_path)
    rc = main(["live-ontogenesis", "--state-dir", state, "--allow-limited-birth"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "first live ontogenesis" in out
    assert "birth gate status" in out


def test_cli_live_concepts(tmp_path, capsys):
    state = _setup(tmp_path)
    main(["live-ontogenesis", "--state-dir", state, "--allow-limited-birth"])
    rc = main(["live-concepts", "--state-dir", state])
    out = capsys.readouterr().out
    assert rc == 0
    assert "live concept memory" in out


def test_cli_live_concept_candidates(tmp_path, capsys):
    state = _setup(tmp_path)
    rc = main(["live-concept-candidates", "--state-dir", state,
               "--allow-limited-birth"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "proto-concept candidates" in out


def test_cli_live_concept_birth_gate(tmp_path, capsys):
    state = _setup(tmp_path)
    rc = main(["live-concept-birth-gate", "--state-dir", state,
               "--allow-limited-birth"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "concept birth gate" in out


def test_cli_strict_nonzero_on_blocker(tmp_path):
    # Require observation stability but provide none -> blocked -> nonzero strict.
    state = str(tmp_path)
    for sub in ("governance", "feeders", "inbox", "certificates"):
        os.makedirs(os.path.join(state, sub), exist_ok=True)
    json.dump(approved_governance(), open(os.path.join(
        state, "governance", "LIVE_READONLY_GOVERNANCE.json"), "w"))
    json.dump(feeder_registry_template(), open(os.path.join(
        state, "feeders", "FEEDER_REGISTRY.json"), "w"))
    rc = main(["live-ontogenesis", "--state-dir", state, "--strict",
               "--require-birth-certificate", "--require-observation-stability"])
    assert rc == 2
