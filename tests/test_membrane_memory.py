"""Membrane memory: append-only, toxicity preserved, repeated quarantine, no deletion."""

from __future__ import annotations

import os

from solaris_ai_nn.environmental_membrane import MembraneMemory


def test_memory_append_only(tmp_path):
    mem = MembraneMemory(state_dir=str(tmp_path))
    mem.update_source("r1", "machine_body", useful=3)
    mem.write()
    history = os.path.join(str(tmp_path), "membrane", "memory",
                           "MEMBRANE_MEMORY_HISTORY.jsonl")
    n1 = sum(1 for _ in open(history))
    mem2 = MembraneMemory(state_dir=str(tmp_path)).load()
    mem2.update_source("r2", "machine_body", useful=1)
    mem2.write()
    n2 = sum(1 for _ in open(history))
    assert n2 > n1


def test_source_toxicity_preserved(tmp_path):
    mem = MembraneMemory(state_dir=str(tmp_path))
    mem.update_source("r1", "mystery", quarantined=2, operator_contamination=1)
    mem.write()
    reloaded = MembraneMemory(state_dir=str(tmp_path)).load()
    m = reloaded.sources["mystery"]
    assert m.toxicity >= 0.5
    assert m.to_dict()["recommend_review"] is True


def test_repeated_quarantine_recorded(tmp_path):
    mem = MembraneMemory(state_dir=str(tmp_path))
    mem.update_source("r1", "mystery", quarantined=2)
    mem.update_source("r2", "mystery", quarantined=1)
    assert mem.sources["mystery"].quarantine_count == 3
    assert mem.index()["toxic_source_count"] >= 1


def test_no_deletion_of_toxic_history(tmp_path):
    mem = MembraneMemory(state_dir=str(tmp_path))
    mem.update_source("r1", "mystery", quarantined=3)
    mem.write()
    # A later clean run does not erase toxicity.
    again = MembraneMemory(state_dir=str(tmp_path)).load()
    again.update_source("r2", "mystery", useful=1)
    assert again.sources["mystery"].toxicity > 0.0
    assert again.sources["mystery"].quarantine_count == 3
