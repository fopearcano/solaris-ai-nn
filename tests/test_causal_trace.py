"""Tests for the CausalTraceBuilder."""

from __future__ import annotations

from solaris_ai_nn.language.causal_trace import HEDGED_RELATIONS, CausalTraceBuilder
from solaris_ai_nn.memory.trace_memory import TraceMemory


def _mock_trace() -> TraceMemory:
    tm = TraceMemory()
    tm.record_event(1, "Stimulus", payload="light")
    tm.record_action(1, "approach", confidence=0.6)
    tm.record_reaction(1, 1.0, error=0.2)
    tm.record_event(2, "Stimulus", payload="noise")
    tm.record_action(2, "withdraw", confidence=0.5)
    tm.record_reaction(2, -1.0, error=0.4)
    return tm


def test_builds_causal_links_from_mock_trace():
    builder = CausalTraceBuilder()
    chain = builder.build_from_recent_trace(_mock_trace())
    assert len(chain.links) > 0
    sources = [l.source for l in chain.links]
    assert any("Stimulus" in s for s in sources)
    targets = [l.target for l in chain.links]
    assert "readout update" in targets and "habit reinforcement" in targets


def test_links_include_confidence_and_hedging():
    builder = CausalTraceBuilder()
    chain = builder.build_from_recent_trace(_mock_trace())
    for link in chain.links:
        assert 0.0 < link.confidence <= 1.0
        if link.confidence < 0.99:
            assert link.relation in HEDGED_RELATIONS  # never a hard causal verb
        else:
            # Direct 'caused' links must name the coded mechanism.
            assert "mechanism" in link.metadata


def test_heuristic_link_cannot_claim_caused():
    builder = CausalTraceBuilder()
    link = builder.link("a", "b", "caused", confidence=0.5)
    assert link.relation != "caused"  # downgraded to a hedged relation


def test_explanation_does_not_overclaim():
    builder = CausalTraceBuilder()
    chain = builder.build_from_recent_trace(_mock_trace())
    explanation = builder.explain_chain(chain.chain_id)
    assert "not proven causation" in explanation.text
    assert explanation.confidence <= 1.0
    missing = builder.explain_chain("nope")
    assert "does not know" in missing.text
    assert missing.confidence == 0.0
