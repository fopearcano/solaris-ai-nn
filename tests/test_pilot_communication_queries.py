"""Pilot-1 <-> Communication: the 9 pilot queries, grounded and safe."""

from __future__ import annotations

from solaris_ai_nn.communication.input_classifier import OperatorInputClassifier
from solaris_ai_nn.communication.query_router import QueryRouter

_STATUS = {
    "pilot_phase": "preflight", "pilot_mode": "plan_only",
    "exit_recommendation": "continue", "uptime_ratio": 1.0,
    "active_failure_modes": [], "dashboard_path": "/x/dashboard.md",
    "daily_review_path": "/x/daily/day_001.md", "weekly_review_path": None,
}


def _ask(text, components=None):
    router = QueryRouter(components=components or {"pilot": _STATUS})
    clf = OperatorInputClassifier()
    return router.route_query(clf.classify(text))


def test_pilot_phase_grounded():
    r = _ask("what pilot phase is active?")
    assert "preflight" in r.text
    assert any("pilot" in ref for ref in r.evidence_refs)


def test_pilot_health():
    assert "recommendation" in _ask("is the pilot healthy?").text


def test_pilot_dashboard():
    assert "dashboard.md" in _ask("show pilot dashboard").text


def test_what_happened_today():
    assert "daily" in _ask("what happened today?").text


def test_weekly_review():
    assert "weekly" in _ask("what is the latest weekly review?").text


def test_failure_modes():
    assert "failure modes" in _ask("what failure modes are active?").text


def test_should_continue():
    assert "watchdog" in _ask("should the pilot continue?").text


def test_simulated_or_real():
    assert "SIMULATED" in _ask("is this simulated or real month-scale?").text


def test_start_30d_requires_approval():
    # Safe even with no pilot component attached.
    r = _ask("can I start the 30-day run?", components={})
    assert "governance approval" in r.text
    assert "must not start it automatically" in r.text
