"""Tests for language schemas (serialization)."""

from __future__ import annotations

from solaris_ai_nn.language.schemas import (
    CausalLink,
    CausalTrace,
    Explanation,
    ExperimentReport,
    MeaningAtom,
    MeaningTrace,
    QueryResult,
    SystemUtterance,
)


def test_meaning_atom_serializes():
    a = MeaningAtom(category="signal", subject="Stimulus", predicate="received",
                    value="from world", confidence=0.9, source_module="bridge",
                    source_signal_id=42, metadata={"x": 1})
    d = a.to_dict()
    for key in ("atom_id", "timestamp", "category", "subject", "predicate",
                "value", "confidence", "source_module", "source_signal_id",
                "metadata"):
        assert key in d
    assert d["source_signal_id"] == 42
    assert "Stimulus received" in a.sentence()


def test_meaning_trace_serializes():
    trace = MeaningTrace(atoms=[
        MeaningAtom(category="signal", subject="s", predicate="received")])
    d = trace.to_dict()
    assert d["atom_count"] == 1
    assert d["atoms"][0]["subject"] == "s"


def test_explanation_serializes():
    e = Explanation(topic="t", text="x happened", grounded_in=["a.b"],
                    unknowns=["c"], confidence=0.5)
    d = e.to_dict()
    assert d["topic"] == "t" and d["grounded_in"] == ["a.b"]
    assert d["unknowns"] == ["c"] and d["confidence"] == 0.5


def test_experiment_report_serializes():
    r = ExperimentReport(title="T", metadata={"m": 1},
                         sections={"s": {"k": 2}}, limitations=["l"])
    d = r.to_dict()
    assert d["title"] == "T" and d["sections"]["s"]["k"] == 2
    assert d["limitations"] == ["l"]


def test_other_schemas_serialize():
    assert CausalLink("a", "b", "preceded", 0.7).to_dict()["confidence"] == 0.7
    assert "links" in CausalTrace().to_dict()
    assert SystemUtterance(kind="k", text="t").to_dict()["grounded"] is True
    qr = QueryResult(query="q", answered=False, text="no")
    assert qr.to_dict()["answered"] is False
