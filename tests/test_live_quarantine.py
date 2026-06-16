"""Live quarantine: record created, original preserved, report generated."""

from __future__ import annotations

import os

from solaris_ai_nn.live_birth import QuarantineReason, QuarantineStore


def test_quarantine_record_created(tmp_path):
    store = QuarantineStore(state_dir=str(tmp_path))
    store.add(QuarantineReason.IS_COMMAND_TRUE, source_file="f.jsonl",
              line_number=2, original={"event_id": "e1"}, event_id="e1")
    assert store.index()["quarantined_event_count"] == 1
    assert store.counts()[QuarantineReason.IS_COMMAND_TRUE] == 1


def test_original_preserved(tmp_path):
    store = QuarantineStore(state_dir=str(tmp_path))
    original = {"event_id": "e1", "payload": {"x": 1}}
    rec = store.add(QuarantineReason.CONTAINS_SECRET, source_file="f.jsonl",
                    line_number=1, original=original, event_id="e1")
    assert rec.original == original
    assert rec.to_dict()["entered_membrane"] is False


def test_report_generated(tmp_path):
    store = QuarantineStore(state_dir=str(tmp_path))
    store.add(QuarantineReason.SOURCE_FORBIDDEN, source_file="f.jsonl",
              line_number=1, original={}, event_id="e1")
    paths = store.write()
    assert os.path.isfile(paths["index"])
    assert os.path.isfile(paths["report"])
    with open(paths["report"], encoding="utf-8") as fh:
        text = fh.read()
    assert "evidence, not deletion" in text


def test_unknown_reason_normalized(tmp_path):
    store = QuarantineStore(state_dir=str(tmp_path))
    rec = store.add("not_a_reason", source_file="f.jsonl", line_number=1,
                    original={})
    assert rec.reason == QuarantineReason.UNKNOWN
