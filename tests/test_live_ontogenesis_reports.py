"""Live ontogenesis reports: all generated, safety boundaries, ClaimGuard-safe."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.live_birth import approved_governance, feeder_registry_template
from solaris_ai_nn.live_observation import PostBirthLiveObservationRuntime
from solaris_ai_nn.live_ontogenesis import FirstLiveOntogenesisRuntime

try:
    from solaris_ai_nn.governance.compliance import ClaimGuard
    _HAS_GUARD = True
except Exception:  # pragma: no cover
    _HAS_GUARD = False


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


def _run(tmp_path):
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
    FirstLiveOntogenesisRuntime(state_dir=state, allow_limited_birth=True).run()
    return state


def test_all_reports_generated(tmp_path):
    state = _run(tmp_path)
    base = os.path.join(state, "ontogenesis", "reports")
    for name in ("LIVE_ONTOGENESIS_REPORT.md", "FEATURE_EXTRACTION_REPORT.md",
                 "RECURRENCE_REPORT.md", "PROTO_CONCEPT_CANDIDATES.md",
                 "STABILITY_SCORING_REPORT.md", "CONTAMINATION_REPORT.md",
                 "CONCEPT_BIRTH_GATE_REPORT.md", "LIVE_CONCEPT_MEMORY_REPORT.md"):
        assert os.path.isfile(os.path.join(base, name)), name


def test_safety_boundaries_in_report(tmp_path):
    state = _run(tmp_path)
    md = open(os.path.join(state, "ontogenesis", "reports",
                           "LIVE_ONTOGENESIS_REPORT.md")).read().lower()
    assert "no semiogenesis was enabled by default" in md
    assert "no feeder was started" in md
    assert "no consciousness/life/agency claim is made" in md


def test_reports_are_claimguard_safe(tmp_path):
    if not _HAS_GUARD:
        return
    state = _run(tmp_path)
    base = os.path.join(state, "ontogenesis")
    for root, _, files in os.walk(base):
        for f in files:
            if f.endswith(".md"):
                txt = open(os.path.join(root, f)).read()
                assert ClaimGuard().scan_text(txt).safe, f
