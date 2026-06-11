"""Tests for the LLM summarizer."""

from __future__ import annotations

from solaris_ai_nn.llm_adapter.mock_client import MockLLMAdapter
from solaris_ai_nn.llm_adapter.summary import LLMSummarizer, _flatten_facts


def test_summarizes_structured_report():
    summarizer = LLMSummarizer(adapter=MockLLMAdapter())
    summary = summarizer.summarize({
        "steps": 120, "health_level": "ok", "incident_count": 0},
        kind="ops_status")
    assert summary
    assert summarizer.summaries_accepted == 1


def test_preserves_limitations():
    summarizer = LLMSummarizer(adapter=MockLLMAdapter())
    summary = summarizer.summarize({
        "steps": 50, "limitation": "bounded run only",
        "uncertain": "anchors incomplete"})
    lowered = summary.lower()
    assert "limitation" in lowered or "uncertain" in lowered


def test_preserves_incident_counts():
    summarizer = LLMSummarizer(adapter=MockLLMAdapter())
    summary = summarizer.summarize({"incident_count": 3,
                                    "health_level": "warning"})
    assert "3" in summary
    assert "incident" in summary.lower()


def test_unsafe_summary_falls_back():
    summarizer = LLMSummarizer(
        adapter=MockLLMAdapter(force_unsafe_output=True))
    summary = summarizer.summarize({"steps": 10, "incident_count": 1})
    # Fallback is the deterministic flattening: facts, not prose.
    assert "steps=10" in summary
    assert "conscious" not in summary
    assert summarizer.summaries_rejected == 1


def test_flatten_facts_deterministic():
    facts = _flatten_facts({"a": 1, "b": {"x": 1}, "c": [1, 2]})
    assert "a=1" in facts
    assert "b has 1 entries" in facts
    assert "c has 2 entries" in facts
    assert _flatten_facts("line1\nline2") == ["line1", "line2"]
