"""Live birth runtime: bounded, governance required, counts, certificate, no control."""

from __future__ import annotations

import inspect
import json
import os

from solaris_ai_nn.live_birth import (
    LiveReadOnlyBirthRuntime,
    approved_governance,
    feeder_registry_template,
    governance_template,
)


def _setup(tmp_path, gov, events=True):
    state = str(tmp_path)
    rt = LiveReadOnlyBirthRuntime(state_dir=state, require_governance=True)
    rt.initialize()
    with open(os.path.join(state, "governance",
                           "LIVE_READONLY_GOVERNANCE.json"), "w") as fh:
        json.dump(gov, fh)
    with open(os.path.join(state, "feeders", "FEEDER_REGISTRY.json"), "w") as fh:
        json.dump(feeder_registry_template(), fh)
    if events:
        good = {"event_id": "e1", "timestamp_utc": "2026-06-16T18:00:00Z",
                "source_id": "chronos_absence", "modality": "chronos",
                "channel": "time", "read_only": True, "is_command": False,
                "human_label_is_ground_truth": False, "payload": {"tick": 1},
                "quality": {"completeness": 1.0, "noise": 0.0,
                            "is_absence": True, "is_noisy": False},
                "safety": {"private_data": False, "contains_instruction": False,
                           "contains_secret": False, "allow_learning": False}}
        bad = dict(good)
        bad = json.loads(json.dumps(good))
        bad["event_id"] = "e2"
        bad["is_command"] = True
        with open(os.path.join(state, "inbox", "events.jsonl"), "w") as fh:
            fh.write(json.dumps(good) + "\n")
            fh.write(json.dumps(bad) + "\n")
    return LiveReadOnlyBirthRuntime(state_dir=state, require_governance=True)


def test_bounded_runtime(tmp_path):
    rt = _setup(tmp_path, approved_governance())
    assert rt.run()["refused"] is False


def test_unbounded_refused(tmp_path):
    rt = LiveReadOnlyBirthRuntime(state_dir=str(tmp_path), max_runtime_s=0)
    assert rt.run()["refused"] is True


def test_governance_required_blocks(tmp_path):
    rt = _setup(tmp_path, governance_template(), events=True)  # SAFE-OFF
    result = rt.run()
    assert result["blocked"] is True
    assert result["accepted_event_count"] == 0


def test_accepted_and_quarantined_counts(tmp_path):
    rt = _setup(tmp_path, approved_governance())
    result = rt.run()
    assert result["blocked"] is False
    assert result["accepted_event_count"] == 1
    assert result["quarantined_event_count"] == 1


def test_birth_certificate_generated(tmp_path):
    rt = _setup(tmp_path, approved_governance())
    rt.run()
    cert_dir = os.path.join(str(tmp_path), "certificates")
    certs = [f for f in os.listdir(cert_dir) if f.endswith(".md")]
    assert certs


def test_status_flags_no_control(tmp_path):
    rt = _setup(tmp_path, approved_governance())
    rt.run()
    st = rt.live_birth_status()
    assert st["starts_feeders"] is False
    assert st["controls_hardware"] is False
    assert st["accesses_network"] is False
    assert st["runs_git"] is False
    assert st["calls_github"] is False


def test_no_network_shell_git_in_source():
    import solaris_ai_nn.live_birth.birth_runtime as runtime

    src = inspect.getsource(runtime)
    assert "subprocess" not in src
    assert "import requests" not in src
    assert "os.system" not in src
    assert "urllib" not in src
