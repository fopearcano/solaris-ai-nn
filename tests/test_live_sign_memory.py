"""Live sign memory: append-only; rejected/contaminated preserved; secrets safe."""

from __future__ import annotations

import os

from solaris_ai_nn.live_semiogenesis import LiveSignMemory, LiveSignRecord


def _record(sid, status, concepts=("c1",), token="sig_live_abc"):
    return LiveSignRecord(sign_id=sid, private_token=token, status=status,
                          run_id="r1", linked_concept_ids=list(concepts))


def test_sign_memory_append_only(tmp_path):
    mem = LiveSignMemory(state_dir=str(tmp_path))
    mem.add(_record("s1", "born"))
    mem.write()
    history = os.path.join(str(tmp_path), "semiogenesis", "signs",
                           "LIVE_SIGN_HISTORY.jsonl")
    n1 = sum(1 for _ in open(history))
    mem2 = LiveSignMemory(state_dir=str(tmp_path))
    mem2.add(_record("s2", "rejected"))
    mem2.write()
    n2 = sum(1 for _ in open(history))
    assert n2 > n1


def test_rejected_and_contaminated_preserved(tmp_path):
    mem = LiveSignMemory(state_dir=str(tmp_path))
    mem.add(_record("s1", "born"))
    mem.add(_record("s2", "rejected"))
    mem.add(_record("s3", "contaminated"))
    index = mem.index().to_dict()
    assert index["by_status"].get("rejected") == 1
    assert index["by_status"].get("contaminated") == 1


def test_born_without_evidence_downgraded(tmp_path):
    mem = LiveSignMemory(state_dir=str(tmp_path))
    rec = mem.add(_record("s1", "born", concepts=()))
    assert rec.status != "born"


def test_secret_token_never_stored(tmp_path):
    mem = LiveSignMemory(state_dir=str(tmp_path))
    mem.add(_record("s1", "born", token="api_key=hunter2"))
    d = mem.index().to_dict()["records"][0]
    assert "hunter2" not in d["private_token"]
    assert d["private_token"].startswith("sig_live_redacted")
