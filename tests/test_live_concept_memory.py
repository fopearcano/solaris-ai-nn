"""Live concept memory: append-only; preserves false starts; evidence required."""

from __future__ import annotations

import os

from solaris_ai_nn.live_ontogenesis import LiveConceptMemory, LiveConceptRecord


def _record(cid, status, support=("e1",)):
    return LiveConceptRecord(
        concept_id=cid, feature_signature="s", status=status, run_id="r1",
        supporting_event_ids=list(support))


def test_concept_memory_append_only(tmp_path):
    mem = LiveConceptMemory(state_dir=str(tmp_path))
    mem.add(_record("c1", "born"))
    mem.write()
    history = os.path.join(str(tmp_path), "ontogenesis", "concepts",
                           "LIVE_CONCEPT_HISTORY.jsonl")
    n1 = sum(1 for _ in open(history))
    mem2 = LiveConceptMemory(state_dir=str(tmp_path))
    mem2.add(_record("c2", "rejected"))
    mem2.write()
    n2 = sum(1 for _ in open(history))
    assert n2 > n1  # history only grows


def test_rejected_and_contaminated_preserved(tmp_path):
    mem = LiveConceptMemory(state_dir=str(tmp_path))
    mem.add(_record("c1", "born"))
    mem.add(_record("c2", "rejected"))
    mem.add(_record("c3", "contaminated"))
    index = mem.index().to_dict()
    assert index["by_status"].get("rejected") == 1
    assert index["by_status"].get("contaminated") == 1


def test_born_without_evidence_downgraded(tmp_path):
    mem = LiveConceptMemory(state_dir=str(tmp_path))
    rec = mem.add(_record("c1", "born", support=()))
    assert rec.status != "born"  # a born record must link to evidence


def test_records_link_to_evidence(tmp_path):
    mem = LiveConceptMemory(state_dir=str(tmp_path))
    mem.add(_record("c1", "born", support=("e1", "e2")))
    d = mem.index().to_dict()["records"][0]
    assert d["supporting_event_ids"] == ["e1", "e2"]
