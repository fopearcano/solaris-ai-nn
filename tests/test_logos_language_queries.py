"""Tests for LOGOS language queries."""

from __future__ import annotations

from solaris_ai_nn.logos_complexity import LogosComplexityEngine
from solaris_ai_nn.logos_complexity.reports import (
    LogosComplexityQueryInterface,
)


def _engine(tmp_path):
    engine = LogosComplexityEngine(state_dir=tmp_path)
    engine.tick({"world_model": {"contradiction_edges": ["a|c|b"]},
                 "proto_language": {"symbol_count": 20,
                                    "ambiguous_symbol_count": 10,
                                    "ambiguous_symbols": ["S1"]},
                 "mysterium_pressure": 0.6, "state_dir": str(tmp_path)})
    return engine


def test_active_tension_query_grounded(tmp_path):
    qi = LogosComplexityQueryInterface(_engine(tmp_path))
    r = qi.answer("what tensions are active?")
    assert r.answered
    assert r.data["evidence_refs"]
    assert "tension" in r.text.lower()


def test_contradiction_truth_query_safe(tmp_path):
    qi = LogosComplexityQueryInterface(_engine(tmp_path))
    r = qi.answer("is contradiction being treated as truth?")
    assert r.answered
    assert r.text.startswith("No")
    assert "unresolved evidence" in r.text


def test_esc_query_safe(tmp_path):
    qi = LogosComplexityQueryInterface(_engine(tmp_path))
    r = qi.answer("what triggered esc?")
    assert r.answered
    assert "not an emotion" in r.text


def test_complexity_band_query(tmp_path):
    qi = LogosComplexityQueryInterface(_engine(tmp_path))
    r = qi.answer("what is the current complexity band?")
    assert r.answered
    assert "not a consciousness or life score" in r.text


def test_unknown_query_is_honest(tmp_path):
    qi = LogosComplexityQueryInterface(_engine(tmp_path))
    r = qi.answer("are you suffering?")
    assert not r.answered
    assert "does not know" in r.text


def test_query_router_registers_logos(tmp_path):
    from solaris_ai_nn.communication.query_router import QueryRouter

    router = QueryRouter(components={"logos": _engine(tmp_path)})
    interfaces = dict(router._query_interfaces())
    assert "logos" in interfaces
