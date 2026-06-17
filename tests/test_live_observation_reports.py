"""Live observation reports + first-day record: disclaimers, ClaimGuard-safe."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.live_birth import approved_governance, feeder_registry_template
from solaris_ai_nn.live_observation import PostBirthLiveObservationRuntime

try:
    from solaris_ai_nn.governance.compliance import ClaimGuard
    _HAS_GUARD = True
except Exception:  # pragma: no cover
    _HAS_GUARD = False


def _ev(eid, ts, sid):
    return {"event_id": eid, "timestamp_utc": ts, "source_id": sid,
            "modality": "scalar", "channel": "c", "read_only": True,
            "is_command": False, "human_label_is_ground_truth": False,
            "payload": {"v": 1},
            "quality": {"completeness": 1.0, "noise": 0.0, "is_absence": False,
                        "is_noisy": False},
            "safety": {"private_data": False, "contains_instruction": False,
                       "contains_secret": False, "allow_learning": False}}


def _run(tmp_path):
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
                                 "operator_pulse"]):
            fh.write(json.dumps(_ev(f"e{i}", f"2026-06-17T08:0{i}:00Z",
                                    sid)) + "\n")
    rt = PostBirthLiveObservationRuntime(state_dir=state)
    rt.run()
    return state


def test_report_set_written(tmp_path):
    state = _run(tmp_path)
    base = os.path.join(state, "observation", "reports")
    for name in ("LIVE_OBSERVATION_REPORT.md", "SOURCE_HEALTH_REPORT.md",
                 "SOURCE_DIET_REPORT.md", "RHYTHM_ABSENCE_REPORT.md",
                 "OVERLOAD_DEPRIVATION_REPORT.md",
                 "METABOLISM_CALIBRATION_REPORT.md", "STABILITY_GATE_REPORT.md"):
        assert os.path.isfile(os.path.join(base, name)), name


def test_main_report_states_what_it_does_not_do(tmp_path):
    state = _run(tmp_path)
    md = open(os.path.join(state, "observation", "reports",
                           "LIVE_OBSERVATION_REPORT.md")).read().lower()
    assert "does not" in md or "not learn" in md
    assert "nothing was learned" in md or "no concept" in md


def test_first_day_record_has_disclaimer(tmp_path):
    state = _run(tmp_path)
    fd = os.path.join(state, "observation", "first_day")
    md = [f for f in os.listdir(fd) if f.endswith(".md")][0]
    text = open(os.path.join(fd, md)).read().lower()
    assert "operational" in text
    assert "not a birth in any" in text or "biological" in text


def test_reports_are_claimguard_safe(tmp_path):
    if not _HAS_GUARD:
        return
    state = _run(tmp_path)
    base = os.path.join(state, "observation")
    for root, _, files in os.walk(base):
        for f in files:
            if f.endswith(".md"):
                txt = open(os.path.join(root, f)).read()
                assert ClaimGuard().scan_text(txt).safe, f
