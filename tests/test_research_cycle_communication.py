"""Research cycle communication: classification + mandated safe answers."""

from __future__ import annotations

from solaris_ai_nn.communication.input_classifier import OperatorInputClassifier
from solaris_ai_nn.communication.query_router import (
    AVAILABLE_QUERIES,
    QueryRouter,
)


def _route(question, components=None):
    cls = OperatorInputClassifier().classify(question)
    return cls, QueryRouter(components=components or {}).route_query(cls)


def test_topics_classified_with_rc_prefix():
    for q, topic in (
            ("where is the research program in its cycle?", "rc_where"),
            ("what is the next action?", "rc_next_action"),
            ("what is blocked?", "rc_blocked"),
            ("what evidence is missing?", "rc_missing_evidence"),
            ("what operator decision is required?", "rc_operator_decision"),
            ("did the cycle complete?", "rc_completed"),
            ("did Solaris approve itself?", "rc_self_approve"),
            ("did Solaris run Git or GitHub?", "rc_git")):
        cls, _ = _route(q)
        assert cls.args.get("topic") == topic, q


def test_next_action_safe_answer():
    _, resp = _route("what is the next action?")
    assert ("recommends the next operator action" in resp.text
            and "does not execute the action" in resp.text)


def test_self_approval_safe_answer():
    _, resp = _route("did Solaris approve itself?")
    assert "Solaris cannot approve itself" in resp.text


def test_git_github_safe_answer():
    _, resp = _route("did Solaris run Git or GitHub?")
    assert "does not run Git" in resp.text
    assert "merge PRs" in resp.text


def test_available_queries_listed():
    assert "what is the next action?" in AVAILABLE_QUERIES
    assert "did Solaris approve itself?" in AVAILABLE_QUERIES


def test_state_query_uses_component():
    component = {"current_cycle_stage": "research_baseline_validated",
                 "current_cycle_status": "completed"}
    _, resp = _route("where is the research program in its cycle?",
                     components={"research_cycle": component})
    assert "research_baseline_validated" in resp.text
