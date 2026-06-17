"""Live ontogenesis consumes birth certificate + observation stability gate."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.live_birth import approved_governance, feeder_registry_template
from solaris_ai_nn.live_observation import PostBirthLiveObservationRuntime
from solaris_ai_nn.live_ontogenesis import FirstLiveOntogenesisRuntime


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


def _base(state, *, cert=True, events=True):
    for sub in ("governance", "feeders", "inbox", "certificates"):
        os.makedirs(os.path.join(state, sub), exist_ok=True)
    json.dump(approved_governance(), open(os.path.join(
        state, "governance", "LIVE_READONLY_GOVERNANCE.json"), "w"))
    json.dump(feeder_registry_template(), open(os.path.join(
        state, "feeders", "FEEDER_REGISTRY.json"), "w"))
    if cert:
        open(os.path.join(state, "certificates", "c.md"), "w").write("# c\n")
    if events:
        rows = [_ev(f"b{i}", f"2026-06-18T08:0{i}:00Z", "machine_body",
                    "machine_body/load", {"load": 0.3}) for i in range(5)]
        rows += [_ev(f"w{i}", f"2026-06-18T08:1{i}:00Z",
                     "local_weather_readonly_external", "weather/t", {"t": 19})
                 for i in range(4)]
        with open(os.path.join(state, "inbox", "ev.jsonl"), "w") as fh:
            for e in rows:
                fh.write(json.dumps(e) + "\n")


def test_consumes_birth_certificate(tmp_path):
    state = str(tmp_path)
    _base(state, cert=True)
    PostBirthLiveObservationRuntime(state_dir=state).run()
    rt = FirstLiveOntogenesisRuntime(state_dir=state,
                                     require_birth_certificate=True)
    rt.run()
    assert rt.birth_certificate_present is True


def test_missing_birth_certificate_blocks(tmp_path):
    state = str(tmp_path)
    _base(state, cert=False)
    PostBirthLiveObservationRuntime(state_dir=state).run()
    rt = FirstLiveOntogenesisRuntime(state_dir=state,
                                     require_birth_certificate=True)
    res = rt.run()
    assert res["blocked"] is True
    assert any("birth certificate" in b for b in res["blockers"])


def test_consumes_observation_stability(tmp_path):
    state = str(tmp_path)
    _base(state)
    PostBirthLiveObservationRuntime(state_dir=state).run()
    rt = FirstLiveOntogenesisRuntime(state_dir=state,
                                     require_observation_stability=True)
    rt.run()
    assert rt.observation["present"] is True


def test_blocked_observation_blocks_ontogenesis(tmp_path):
    # An operator-dominated field makes the observation stability gate block,
    # which must block ontogenesis when required.
    state = str(tmp_path)
    for sub in ("governance", "feeders", "inbox", "certificates"):
        os.makedirs(os.path.join(state, sub), exist_ok=True)
    json.dump(approved_governance(), open(os.path.join(
        state, "governance", "LIVE_READONLY_GOVERNANCE.json"), "w"))
    json.dump(feeder_registry_template(), open(os.path.join(
        state, "feeders", "FEEDER_REGISTRY.json"), "w"))
    open(os.path.join(state, "certificates", "c.md"), "w").write("# c\n")
    rows = [_ev(f"op{i}", f"2026-06-18T08:0{i}:00Z", "operator_pulse",
                "operator/pulse", {"pulse": 1}) for i in range(6)]
    with open(os.path.join(state, "inbox", "ev.jsonl"), "w") as fh:
        for e in rows:
            fh.write(json.dumps(e) + "\n")
    PostBirthLiveObservationRuntime(state_dir=state).run()
    rt = FirstLiveOntogenesisRuntime(state_dir=state,
                                     require_observation_stability=True)
    res = rt.run()
    assert res["blocked"] is True
    assert any("observation" in b for b in res["blockers"])
