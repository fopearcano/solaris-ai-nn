"""Tests for auto-regeneration language queries."""

from __future__ import annotations

from solaris_ai_nn.autoregeneration import AutoRegenerationEngine, RepairPolicy
from solaris_ai_nn.autoregeneration.reports import (
    AutoRegenerationQueryInterface,
)


def _engine(tmp_path):
    engine = AutoRegenerationEngine(
        state_dir=tmp_path, policy=RepairPolicy(mode="safe_auto_repair"))
    engine.tick({"memory": {"over_budget": ["hot"]},
                 "mysterium_pressure": 0.97, "state_dir": str(tmp_path)})
    return engine


def test_degradation_query_grounded(tmp_path):
    qi = AutoRegenerationQueryInterface(_engine(tmp_path))
    r = qi.answer("what degradation was detected?")
    assert r.answered
    assert r.data["evidence_refs"]
    assert "degradation" in r.text.lower()


def test_source_code_repair_answer_safe(tmp_path):
    qi = AutoRegenerationQueryInterface(_engine(tmp_path))
    r = qi.answer("is source code being modified?")
    assert r.answered
    assert r.text.startswith("No.")
    assert "forbidden" in r.text.lower()


def test_refused_repair_query_explains_reason(tmp_path):
    engine = _engine(tmp_path)
    # Force a refused repair into memory, then ask why it was blocked.
    from solaris_ai_nn.autoregeneration.repair_actions import (
        RepairActionType,
        make_repair,
    )
    from solaris_ai_nn.autoregeneration.repair_policy import RepairDecision

    bad = make_repair(RepairActionType.REBUILD_INDEX,
                      target_ref="src/solaris_ai_nn/core.py")
    engine._handle(RepairDecision(action=bad, mode="safe_auto_repair",
                                  apply_allowed=True),
                   {"state_dir": str(engine.state_dir)})
    qi = AutoRegenerationQueryInterface(engine)
    r = qi.answer("why was repair blocked?")
    assert r.answered
    assert "blocked" in r.text.lower()


def test_quarantine_query(tmp_path):
    qi = AutoRegenerationQueryInterface(_engine(tmp_path))
    r = qi.answer("what was quarantined?")
    assert r.answered
    assert "quarantine" in r.text.lower()


def test_unknown_query_is_honest(tmp_path):
    qi = AutoRegenerationQueryInterface(_engine(tmp_path))
    r = qi.answer("are you alive?")
    assert not r.answered
    assert "does not know" in r.text
