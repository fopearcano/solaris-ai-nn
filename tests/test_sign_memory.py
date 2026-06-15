"""SignMemoryStore: append-only; rejected preserved; merge/split recorded."""

from __future__ import annotations

import os

from solaris_ai_nn.semiogenesis import (
    InternalSign,
    SignKind,
    SignMemoryStore,
    SignStatus,
)


def test_append_only_signs(tmp_path):
    store = SignMemoryStore(state_dir=str(tmp_path))
    s = InternalSign(kind=SignKind.MODALITY_NATIVE,
                     modality_distribution={"radio_frequency": 3})
    store.record_sign(s.to_dict())
    store.write_index()
    assert os.path.isfile(tmp_path / "signs.jsonl")
    assert os.path.isfile(tmp_path / "sign_index.json")


def test_rejected_sign_preserved(tmp_path):
    store = SignMemoryStore(state_dir=str(tmp_path))
    s = InternalSign(kind=SignKind.UNKNOWN,
                     modality_distribution={"radio_frequency": 1})
    store.record_sign(s.to_dict())
    store.record_sign_state(s.sign_id, SignStatus.REJECTED,
                            {"reason": "false_pattern"})
    history = store.sign_history(s.sign_id)
    assert len(history) == 2  # original + rejection retained
    assert store.index.signs[s.sign_id]["status"] == SignStatus.REJECTED


def test_merge_split_recorded(tmp_path):
    store = SignMemoryStore(state_dir=str(tmp_path))
    s = InternalSign(kind=SignKind.MODALITY_NATIVE,
                     modality_distribution={"radio_frequency": 2})
    store.record_sign(s.to_dict())
    store.record_sign_state(s.sign_id, SignStatus.MERGED, {"into": "SIGN_X"})
    store.record_sign_state(s.sign_id, SignStatus.SPLIT, {"into": ["A", "B"]})
    assert len(store.sign_history(s.sign_id)) == 3


def test_relations_and_utterances_recorded(tmp_path):
    store = SignMemoryStore(state_dir=str(tmp_path))
    store.record_relation({"pattern_id": "SYN_1", "relation": "sequence"})
    store.record_utterance({"utterance_id": "UTT_1", "kind": "prediction"})
    assert os.path.isfile(tmp_path / "sign_relations.jsonl")
    assert os.path.isfile(tmp_path / "utterances.jsonl")
    assert "UTT_1" in store.index.utterance_ids
