"""OperatorSessionLog: events appended; blocked visible; no secrets logged."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.operator_console import (
    OperatorSessionEventType,
    OperatorSessionLog,
)


def test_session_events_appended(tmp_path):
    log = OperatorSessionLog(state_dir=str(tmp_path / "op"))
    log.record(OperatorSessionEventType.CONSOLE_STARTED)
    log.record(OperatorSessionEventType.PROFILE_LISTED, {"count": 60})
    assert os.path.isfile(log.path)
    lines = open(log.path, encoding="utf-8").read().strip().splitlines()
    assert len(lines) == 2


def test_blocked_run_visible(tmp_path):
    log = OperatorSessionLog(state_dir=str(tmp_path / "op"))
    log.record(OperatorSessionEventType.RUN_BLOCKED,
               {"profile_id": "pilot1_30d_soak"})
    blocked = log.blocked_events()
    assert len(blocked) == 1
    assert blocked[0].critical is True


def test_no_secret_content_logged(tmp_path):
    log = OperatorSessionLog(state_dir=str(tmp_path / "op"))
    event = log.record(OperatorSessionEventType.APPROVAL_RECORDED,
                       {"password": "hunter2", "token": "abc",
                        "scope": "bounded_fixture_run"})
    assert event.detail["password"] == "[redacted]"
    assert event.detail["token"] == "[redacted]"
    assert event.detail["scope"] == "bounded_fixture_run"
    raw = open(log.path, encoding="utf-8").read()
    assert "hunter2" not in raw


def test_unknown_event_rejected(tmp_path):
    log = OperatorSessionLog(state_dir=str(tmp_path / "op"))
    try:
        log.record("not_a_real_event")
        assert False, "expected ValueError"
    except ValueError:
        pass
