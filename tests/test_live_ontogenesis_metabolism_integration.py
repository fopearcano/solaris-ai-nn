"""Live ontogenesis uses metabolism thresholds as context; never writes them."""

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


def _setup(tmp_path):
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


def test_uses_metabolism_as_context(tmp_path):
    state = _setup(tmp_path)
    rt = FirstLiveOntogenesisRuntime(state_dir=state, allow_limited_birth=True)
    rt.run()
    # The observation report (which carries metabolism calibration) is consumed.
    assert rt.observation["present"] is True
    assert "metabolism" in rt.observation


def test_does_not_write_metabolism_thresholds(tmp_path):
    state = _setup(tmp_path)
    metab_dir = os.path.join(state, "observation", "metabolism")
    before = sorted(os.listdir(metab_dir)) if os.path.isdir(metab_dir) else []
    FirstLiveOntogenesisRuntime(state_dir=state, allow_limited_birth=True).run()
    after = sorted(os.listdir(metab_dir)) if os.path.isdir(metab_dir) else []
    # Ontogenesis must not modify the observation metabolism calibration state.
    assert before == after
