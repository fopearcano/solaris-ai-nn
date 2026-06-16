"""Live inbox spool: bounded read, max events respected, no deletion, quarantine."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.live_birth import (
    LiveEventValidator,
    LiveInboxSpool,
    QuarantineStore,
)

_ALLOWED = ["chronos_absence", "operator_pulse"]


def _good(i):
    return {"event_id": f"e{i}", "timestamp_utc": "2026-06-16T18:00:00Z",
            "source_id": "chronos_absence", "modality": "chronos",
            "channel": "time", "read_only": True, "is_command": False,
            "human_label_is_ground_truth": False, "payload": {"tick": i},
            "quality": {"completeness": 1.0, "noise": 0.0, "is_absence": False,
                        "is_noisy": False},
            "safety": {"private_data": False, "contains_instruction": False,
                       "contains_secret": False, "allow_learning": False}}


def _spool(tmp_path, max_events=500):
    inbox = os.path.join(str(tmp_path), "inbox")
    os.makedirs(inbox, exist_ok=True)
    validator = LiveEventValidator(allowed_sources=_ALLOWED,
                                   registered_sources=_ALLOWED)
    quarantine = QuarantineStore(state_dir=str(tmp_path))
    return inbox, LiveInboxSpool(inbox_dir=inbox, validator=validator,
                                 quarantine=quarantine, max_events=max_events)


def test_bounded_read(tmp_path):
    inbox, spool = _spool(tmp_path)
    with open(os.path.join(inbox, "a.jsonl"), "w") as fh:
        for i in range(5):
            fh.write(json.dumps(_good(i)) + "\n")
    result = spool.read()
    assert result.event_count == 5
    assert result.accepted_count == 5


def test_max_events_respected(tmp_path):
    inbox, spool = _spool(tmp_path, max_events=3)
    with open(os.path.join(inbox, "a.jsonl"), "w") as fh:
        for i in range(10):
            fh.write(json.dumps(_good(i)) + "\n")
    result = spool.read()
    assert result.event_count == 3
    assert result.truncated is True


def test_no_deletion_of_inbox(tmp_path):
    inbox, spool = _spool(tmp_path)
    path = os.path.join(inbox, "a.jsonl")
    with open(path, "w") as fh:
        fh.write(json.dumps(_good(0)) + "\n")
    spool.read()
    assert os.path.isfile(path)


def test_unsafe_events_quarantined(tmp_path):
    inbox, spool = _spool(tmp_path)
    bad = _good(0)
    bad["is_command"] = True
    with open(os.path.join(inbox, "a.jsonl"), "w") as fh:
        fh.write(json.dumps(bad) + "\n")
        fh.write(json.dumps(_good(1)) + "\n")
    result = spool.read()
    assert result.quarantined_count == 1
    assert result.accepted_count == 1


def test_invalid_json_line_quarantined(tmp_path):
    inbox, spool = _spool(tmp_path)
    with open(os.path.join(inbox, "a.jsonl"), "w") as fh:
        fh.write("{ not valid json\n")
        fh.write(json.dumps(_good(1)) + "\n")
    result = spool.read()
    assert result.quarantined_count == 1
