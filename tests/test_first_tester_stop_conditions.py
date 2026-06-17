"""First tester stop conditions: critical, live, pause, safety blockers visible."""

from __future__ import annotations

from solaris_ai_nn.first_tester_protocol import (
    FirstTesterStopConditions,
    StopSeverity,
)


def test_critical_stop_generated():
    c = FirstTesterStopConditions()
    crit = c.by_severity(StopSeverity.CRITICAL_STOP)
    assert crit
    text = " ".join(x.text for x in crit).lower()
    assert "feeder" in text
    assert "hardware" in text


def test_live_stop_generated():
    c = FirstTesterStopConditions()
    live = c.by_severity(StopSeverity.STOP_LIVE_TESTING)
    text = " ".join(x.text for x in live).lower()
    assert "governance" in text
    assert "membrane" in text


def test_pause_condition_generated():
    c = FirstTesterStopConditions()
    assert c.by_severity(StopSeverity.PAUSE)


def test_safety_blockers_visible(tmp_path):
    path = FirstTesterStopConditions().write(str(tmp_path))
    text = open(path, encoding="utf-8").read().lower()
    assert "critical stop" in text
    assert "never work around a safety blocker" in text
