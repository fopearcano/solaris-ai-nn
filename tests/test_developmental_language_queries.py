"""Tests for the developmental language queries."""

from __future__ import annotations

from solaris_ai_nn.developmental.developmental_runtime import (
    DevelopmentalRuntime,
)
from solaris_ai_nn.developmental.reports import (
    DevelopmentalQueryInterface,
)
from solaris_ai_nn.governance.compliance import ClaimGuard


def _queries(tmp_path):
    runtime = DevelopmentalRuntime(
        state_dir=tmp_path / "dev", simulated_time=True,
        time_acceleration=3600.0, max_steps=60,
        consolidation_interval_steps=30, seed=3)
    runtime.run()
    return runtime, DevelopmentalQueryInterface(runtime)


def test_milestone_query_grounded(tmp_path):
    _, queries = _queries(tmp_path)
    result = queries.answer("what milestones were recorded?")
    assert result.answered
    assert "The runtime recorded" in result.text
    assert "milestone" in result.text
    assert "evidence" in result.text


def test_structural_growth_query_cautious(tmp_path):
    _, queries = _queries(tmp_path)
    growing = queries.answer(
        "is the system growing or just accumulating data?")
    assert growing.answered
    lowered = growing.text.lower()
    assert ("no evidence of structural growth" in lowered
            or "measurement over recorded metrics" in lowered
            or "structural metrics did not move" in lowered)
    structural = queries.answer("what structural changes happened?")
    assert "not proof of emergence" in structural.text


def test_no_emergence_overclaim(tmp_path):
    _, queries = _queries(tmp_path)
    guard = ClaimGuard()
    assert len(queries.supported_queries()) == 8
    for question in queries.supported_queries():
        answer = queries.answer(question)
        assert guard.is_safe(answer.text), question
        lowered = answer.text.lower()
        for forbidden in ("is conscious", "is alive", "emerged",
                          "became aware", "i grew", "i remember"):
            assert forbidden not in lowered, (question, forbidden)


def test_survival_and_epoch_queries(tmp_path):
    _, queries = _queries(tmp_path)
    epoch = queries.answer("what developmental epoch is active?")
    assert "label" in epoch.text
    assert "not proof" in epoch.text
    survived = queries.answer("what survived across restarts?")
    assert "operational runtime continuity" in survived.text
    unknown = queries.answer("did the system wake up?")
    assert not unknown.answered
