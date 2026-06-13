"""Tests for opposition memory."""

from __future__ import annotations

from solaris_ai_nn.logos_complexity.opposition_memory import OppositionMemory
from solaris_ai_nn.logos_complexity.tension import (
    LogosTension,
    TensionPolarity,
    TensionStatus,
    TensionType,
)


def _tension(ttype=TensionType.SYMBOL_AMBIGUITY, node="S1"):
    return LogosTension(tension_type=ttype,
                        polarity_a=TensionPolarity.STABLE,
                        polarity_b=TensionPolarity.AMBIGUOUS,
                        related_world_nodes=[node], evidence_refs=["e"])


def test_records_tension(tmp_path):
    mem = OppositionMemory(state_dir=tmp_path)
    mem.record_tension(_tension())
    assert mem.snapshot()["tension_count"] == 1
    assert (tmp_path / "logos_tensions.jsonl").exists()


def test_records_synthesis_result(tmp_path):
    mem = OppositionMemory(state_dir=tmp_path)
    mem.record_synthesis_result({"applied": True, "refused": False})
    assert mem.successful_synthesis() == 1
    assert (tmp_path / "synthesis_results.jsonl").exists()


def test_recurring_tension_detected(tmp_path):
    mem = OppositionMemory(state_dir=tmp_path)
    for i in range(4):
        # Same dedup key (same type + node) recorded under distinct ids.
        mem.record_tension(_tension(node="S_same"))
    assert mem.recurring()


def test_preserved_and_unresolved(tmp_path):
    mem = OppositionMemory(state_dir=tmp_path)
    t = _tension()
    mem.record_tension(t)
    t.set_status(TensionStatus.PRESERVED)
    mem.record_status(t)
    assert mem.snapshot()["preserved_count"] == 1


def test_persistence(tmp_path):
    mem = OppositionMemory(state_dir=tmp_path)
    mem.record_tension(_tension())
    mem.save_state()
    assert (tmp_path / "opposition_memory.json").exists()


def test_hypothesis_promotion(tmp_path):
    mem = OppositionMemory(state_dir=tmp_path)
    t = _tension(TensionType.WORLD_MODEL_CONTRADICTION)
    mem.record_tension(t)
    t.set_status(TensionStatus.HYPOTHESIS_CREATED)
    mem.record_status(t)
    assert mem.snapshot()["became_hypotheses"] == 1
