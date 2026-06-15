"""IdentityTraceStore: append-only; restart recorded; no personhood language."""

from __future__ import annotations

import os

from solaris_ai_nn.self_boundary import (
    IdentityTraceEventType,
    IdentityTraceStore,
)


def test_append_only_trace(tmp_path):
    store = IdentityTraceStore(state_dir=str(tmp_path))
    store.record_event(IdentityTraceEventType.RUN_IDENTITY,
                       {"run_id": store.trace.run_id})
    store.record_event(IdentityTraceEventType.BOUNDARY_SHIFT, {"x": 1})
    assert os.path.isfile(tmp_path / "identity_trace.jsonl")
    lines = open(tmp_path / "identity_trace.jsonl").read().strip().splitlines()
    assert len(lines) == 2


def test_restart_event_recorded(tmp_path):
    store = IdentityTraceStore(state_dir=str(tmp_path))
    store.record_event(IdentityTraceEventType.RESTART, {"detail": "restart"})
    assert store.trace.restart_events == 1


def test_no_personhood_language(tmp_path):
    store = IdentityTraceStore(state_dir=str(tmp_path))
    d = store.trace.to_dict()
    assert "not personhood" in d["note"]
    assert any("not personal identity" in lim for lim in d["limitations"])


def test_boundary_and_break_events_persisted(tmp_path):
    store = IdentityTraceStore(state_dir=str(tmp_path))
    store.record_boundary_event({"event_id": "BND_1", "zone": "receptor_body"})
    store.record_continuity_break({"break_id": "BRK_1",
                                   "break_type": "source_silence"})
    assert os.path.isfile(tmp_path / "boundary_events.jsonl")
    assert os.path.isfile(tmp_path / "continuity_breaks.jsonl")
