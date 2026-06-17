"""Live ontogenesis record: generated, disclaimer present, blockers visible."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.live_birth import approved_governance, feeder_registry_template
from solaris_ai_nn.live_observation import PostBirthLiveObservationRuntime
from solaris_ai_nn.live_ontogenesis import FirstLiveOntogenesisRuntime


def _ev(eid, ts, sid, channel, payload, noise=0.0, absence=False,
        modality="scalar"):
    return {"event_id": eid, "timestamp_utc": ts, "source_id": sid,
            "modality": modality, "channel": channel, "read_only": True,
            "is_command": False, "human_label_is_ground_truth": False,
            "payload": payload,
            "quality": {"completeness": 1.0, "noise": noise,
                        "is_absence": absence, "is_noisy": False},
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


def test_record_generated(tmp_path):
    state = _setup(tmp_path)
    rt = FirstLiveOntogenesisRuntime(state_dir=state, allow_limited_birth=True)
    rt.run()
    reports = os.path.join(state, "ontogenesis", "reports")
    md = [f for f in os.listdir(reports)
          if f.startswith("LIVE_ONTOGENESIS_RECORD_") and f.endswith(".md")]
    assert md


def test_disclaimer_present(tmp_path):
    state = _setup(tmp_path)
    rt = FirstLiveOntogenesisRuntime(state_dir=state, allow_limited_birth=True)
    rt.run()
    reports = os.path.join(state, "ontogenesis", "reports")
    md = [f for f in os.listdir(reports)
          if f.startswith("LIVE_ONTOGENESIS_RECORD_") and f.endswith(".md")][0]
    text = open(os.path.join(reports, md)).read().lower()
    assert "operational feature-stability records" in text
    assert "do not imply consciousness" in text


def test_blockers_visible(tmp_path):
    # No observation present + require it -> blocked, record still written.
    state = str(tmp_path)
    for sub in ("governance", "feeders", "inbox", "certificates"):
        os.makedirs(os.path.join(state, sub), exist_ok=True)
    json.dump(approved_governance(), open(os.path.join(
        state, "governance", "LIVE_READONLY_GOVERNANCE.json"), "w"))
    json.dump(feeder_registry_template(), open(os.path.join(
        state, "feeders", "FEEDER_REGISTRY.json"), "w"))
    rt = FirstLiveOntogenesisRuntime(state_dir=state,
                                     require_birth_certificate=True,
                                     require_observation_stability=True)
    result = rt.run()
    assert result["blocked"] is True
    assert result["blockers"]
