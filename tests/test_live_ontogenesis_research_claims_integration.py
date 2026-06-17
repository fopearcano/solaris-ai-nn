"""Live ontogenesis research/claims integration: evidence recorded, operational only."""

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


def _run(tmp_path, allow_birth):
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
    PostBirthLiveObservationRuntime(state_dir=state).run()
    rt = FirstLiveOntogenesisRuntime(state_dir=state,
                                     allow_limited_birth=allow_birth)
    rt.run()
    return rt


def test_research_cycle_evidence_recorded(tmp_path):
    rt = _run(tmp_path, allow_birth=True)
    update = rt.research_cycle_update()
    assert update["ontogenesis_evidence_recorded"] is True
    assert update["next_action"] in (
        "Prepare live semiogenesis protocol", "Resolve ontogenesis blockers",
        "Continue live ontogenesis observation")
    assert update["operational_only"] is True


def test_claims_marked_operational_only(tmp_path):
    rt = _run(tmp_path, allow_birth=True)
    claims = rt.scientific_claims_update()
    assert claims["evidence_kind"] == "operational_feature_stability_record"
    assert claims["inconclusive_for_consciousness"] is True
    assert claims["blocks_consciousness_life_agency_interpretation"] is True


def test_candidate_only_run_marked_inconclusive(tmp_path):
    rt = _run(tmp_path, allow_birth=False)
    claims = rt.scientific_claims_update()
    assert claims["candidate_only_run"] is True
