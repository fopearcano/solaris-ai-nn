"""Tests for the executive working memory."""

from __future__ import annotations

import json
import time

from solaris_ai_nn.executive.working_memory import WorkingMemory


def test_bounded_items():
    memory = WorkingMemory(max_items=5)
    for i in range(20):
        memory.add("candidate", {"label": f"c{i}"})
    assert len(memory) == 5
    assert memory.recent("candidate")[-1].content["label"] == "c19"


def test_expiration_works():
    memory = WorkingMemory()
    memory.add("desire", {"proposal": "rest"}, ttl_s=0.01)
    memory.add("plan", {"goal": "look"}, ttl_s=60.0)
    time.sleep(0.05)
    assert memory.expire() == 1
    assert len(memory) == 1
    assert memory.recent("plan")


def test_snapshot_serializes():
    memory = WorkingMemory()
    memory.add("inhibition", {"label": "explore_safely",
                              "reason": "safety"})
    memory.add("prospection", {"label": "rest", "outcome": "favorable"})
    memory.set_focus({"target": "low_energy", "priority": 0.7})
    memory.set_mode("arbitrated")
    memory.set_constraints(["no external action during sleep"])
    snap = memory.snapshot()
    json.dumps(snap, default=str)
    assert snap["counts_by_kind"] == {"inhibition": 1, "prospection": 1}
    assert snap["focus"]["target"] == "low_energy"
    assert snap["mode"] == "arbitrated"
    assert snap["constraints"][0].startswith("no external action")
