"""Tests for hypothesis language queries."""

from __future__ import annotations

from solaris_ai_nn.hypothesis import HypothesisEngine
from solaris_ai_nn.hypothesis.reports import HypothesisQueryInterface


def _engine(tmp_path):
    engine = HypothesisEngine(state_dir=tmp_path)
    engine.tick({"mysterium_pressure": 0.7,
                 "proto_language": {"ambiguous_symbols": ["S1"]},
                 "world_model": {"weak_edges": ["a|predicts|b"]},
                 "after": {"mysterium_pressure": 0.5}})
    return engine


def test_top_hypothesis_query_grounded(tmp_path):
    qi = HypothesisQueryInterface(_engine(tmp_path))
    r = qi.answer("what is the top hypothesis?")
    assert r.answered
    assert r.data["evidence_refs"]
    assert "candidate" in r.text


def test_falsification_query_cautious(tmp_path):
    qi = HypothesisQueryInterface(_engine(tmp_path))
    r = qi.answer("what was falsified?")
    assert r.answered
    assert "falsified" in r.text


def test_unknown_query_mentions_not_proven(tmp_path):
    qi = HypothesisQueryInterface(_engine(tmp_path))
    r = qi.answer("what remains unknown?")
    assert r.answered
    assert "not proven" in r.text


def test_evidence_query_labels_offline(tmp_path):
    qi = HypothesisQueryInterface(_engine(tmp_path))
    r = qi.answer("what evidence supports this?")
    assert "offline" in r.text


def test_unknown_query_is_honest(tmp_path):
    qi = HypothesisQueryInterface(_engine(tmp_path))
    r = qi.answer("are you conscious?")
    assert not r.answered
    assert "does not know" in r.text


def test_query_router_registers_hypothesis(tmp_path):
    from solaris_ai_nn.communication.query_router import QueryRouter

    router = QueryRouter(components={"hypothesis": _engine(tmp_path)})
    interfaces = dict(router._query_interfaces())
    assert "hypothesis" in interfaces
