"""Live cognition memory: append-only; failures preserved; evidence required."""

from __future__ import annotations

import os

from solaris_ai_nn.live_cognition import LiveCognitionMemory, LiveCognitionRecord


def _record(tid, status, support=("c1",)):
    return LiveCognitionRecord(trace_id=tid, kind="anticipation", status=status,
                               run_id="r1", linked_sign_ids=["s1"],
                               supporting_refs=list(support))


def test_memory_append_only(tmp_path):
    mem = LiveCognitionMemory(state_dir=str(tmp_path))
    mem.add(_record("t1", "useful"))
    mem.write()
    history = os.path.join(str(tmp_path), "cognition", "traces",
                           "LIVE_COGNITION_HISTORY.jsonl")
    n1 = sum(1 for _ in open(history))
    mem2 = LiveCognitionMemory(state_dir=str(tmp_path))
    mem2.add(_record("t2", "rejected"))
    mem2.write()
    n2 = sum(1 for _ in open(history))
    assert n2 > n1


def test_failures_preserved(tmp_path):
    mem = LiveCognitionMemory(state_dir=str(tmp_path))
    mem.add(_record("t1", "useful"))
    mem.add(_record("t2", "rejected"))
    mem.add(_record("t3", "contaminated"))
    mem.add(_record("t4", "weak"))
    index = mem.index().to_dict()
    assert index["by_status"].get("rejected") == 1
    assert index["by_status"].get("contaminated") == 1
    assert index["by_status"].get("weak") == 1


def test_promoted_without_evidence_downgraded(tmp_path):
    mem = LiveCognitionMemory(state_dir=str(tmp_path))
    rec = mem.add(_record("t1", "useful", support=()))
    assert rec.status != "useful"


def test_evidence_links_required(tmp_path):
    mem = LiveCognitionMemory(state_dir=str(tmp_path))
    mem.add(_record("t1", "useful", support=("c1", "c2")))
    d = mem.index().to_dict()["records"][0]
    assert d["supporting_refs"] == ["c1", "c2"]
