"""Tests for hypothesis memory."""

from __future__ import annotations

from solaris_ai_nn.hypothesis.hypotheses import (
    Hypothesis,
    HypothesisStatus,
    HypothesisType,
)
from solaris_ai_nn.hypothesis.hypothesis_memory import (
    LONG_LIVED_THRESHOLD,
    HypothesisMemory,
)


def _hyp(htype=HypothesisType.PREDICTION, target="t"):
    return Hypothesis(type=htype, statement="s", target_ref=target)


def test_stores_proposed(tmp_path):
    memory = HypothesisMemory(state_dir=tmp_path)
    h = _hyp()
    memory.add(h)
    assert memory.snapshot()["hypothesis_count"] == 1
    assert memory.counts_by_status()[HypothesisStatus.PROPOSED] == 1


def test_stores_tested_and_falsified(tmp_path):
    memory = HypothesisMemory(state_dir=tmp_path)
    h = _hyp()
    memory.add(h)
    h.set_status(HypothesisStatus.FALSIFIED)
    memory.record_status(h, "failed test")
    assert memory.by_status(HypothesisStatus.FALSIFIED)


def test_long_lived_unknown_tracked(tmp_path):
    memory = HypothesisMemory(state_dir=tmp_path)
    old = _hyp(target="old")
    memory.add(old)
    # Age out by adding many other hypotheses.
    for i in range(LONG_LIVED_THRESHOLD + 2):
        memory.add(_hyp(HypothesisType.WORLD_MODEL_EDGE, target=f"e{i}"))
    assert old in memory.long_lived_unknowns()


def test_persistence_works(tmp_path):
    memory = HypothesisMemory(state_dir=tmp_path)
    memory.add(_hyp())
    memory.save_state()
    assert (tmp_path / "hypotheses.json").exists()
    assert (tmp_path / "hypothesis_history.jsonl").exists()


def test_promotion_recorded(tmp_path):
    memory = HypothesisMemory(state_dir=tmp_path)
    h = _hyp()
    memory.add(h)
    memory.record_promotion(h.hypothesis_id, "world_model")
    assert h.hypothesis_id in memory.promoted_to_world_model


def test_family_counts(tmp_path):
    memory = HypothesisMemory(state_dir=tmp_path)
    memory.add(_hyp(HypothesisType.PREDICTION, "a"))
    memory.add(_hyp(HypothesisType.WORLD_MODEL_EDGE, "b"))
    fams = memory.family_counts()
    assert fams[HypothesisType.PREDICTION] == 1
    assert fams[HypothesisType.WORLD_MODEL_EDGE] == 1
