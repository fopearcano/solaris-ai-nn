"""Live birth reports: all generated, safety boundaries, ClaimGuard if available."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.live_birth import (
    LiveReadOnlyBirthRuntime,
    approved_governance,
    feeder_registry_template,
)


def _run(tmp_path):
    state = str(tmp_path)
    rt = LiveReadOnlyBirthRuntime(state_dir=state, require_governance=True)
    rt.initialize()
    with open(os.path.join(state, "governance",
                           "LIVE_READONLY_GOVERNANCE.json"), "w") as fh:
        json.dump(approved_governance(), fh)
    with open(os.path.join(state, "feeders", "FEEDER_REGISTRY.json"), "w") as fh:
        json.dump(feeder_registry_template(), fh)
    good = {"event_id": "e1", "timestamp_utc": "2026-06-16T18:00:00Z",
            "source_id": "chronos_absence", "modality": "chronos",
            "channel": "time", "read_only": True, "is_command": False,
            "human_label_is_ground_truth": False, "payload": {"tick": 1},
            "quality": {"completeness": 1.0, "noise": 0.0, "is_absence": True,
                        "is_noisy": False},
            "safety": {"private_data": False, "contains_instruction": False,
                       "contains_secret": False, "allow_learning": False}}
    with open(os.path.join(state, "inbox", "e.jsonl"), "w") as fh:
        fh.write(json.dumps(good) + "\n")
    rt.run()
    return rt


def test_all_reports_generated(tmp_path):
    rt = _run(tmp_path)
    out = rt.write_artifacts()
    names = {os.path.basename(p) for p in out["documents"]}
    for expected in ("LIVE_BIRTH_REPORT.md", "LIVE_BIRTH_REPORT.json",
                     "FIRST_CONTACT_REPORT.md", "LIVE_EVENT_VALIDATION_REPORT.md",
                     "LIVE_MEMBRANE_ACTIVATION_REPORT.md",
                     "LIVE_BIRTH_SAFETY_REPORT.md"):
        assert expected in names


def test_safety_boundaries_included(tmp_path):
    rt = _run(tmp_path)
    rt.write_artifacts()
    with open(os.path.join(str(tmp_path), "reports", "LIVE_BIRTH_REPORT.md"),
              encoding="utf-8") as fh:
        text = fh.read().lower()
    assert "no feeder was started" in text
    assert "no hardware was controlled" in text
    assert "no consciousness/life/agency claim is made" in text


def test_claim_guard_scan_if_available(tmp_path):
    rt = _run(tmp_path)
    report = rt.write_artifacts()["report"]
    assert report["claim_guard_safe"] is True
