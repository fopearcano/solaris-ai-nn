"""First tester integration: blocked RC/packaging/safety freeze block the session."""

from __future__ import annotations

from _first_tester_helpers import (
    run_protocol,
    seed_packaging_blocked,
    seed_rc,
    seed_safety_blocked,
)


def test_blocked_rc_marks_session_blocked(tmp_path):
    base = str(tmp_path / "rc")
    seed_rc(base, "critical_blocked")
    rt = run_protocol(base)
    assert rt.session_status() == "blocked"
    assert rt.blockers


def test_packaging_blocker_marks_session_blocked(tmp_path):
    base = str(tmp_path / "pkg")
    seed_packaging_blocked(base)
    rt = run_protocol(base)
    assert rt.session_status() == "blocked"
    assert any("packaging" in b for b in rt.blockers)


def test_safety_freeze_blocker_marks_session_blocked(tmp_path):
    base = str(tmp_path / "sf")
    seed_safety_blocked(base)
    rt = run_protocol(base)
    assert rt.session_status() == "blocked"
    assert any("safety" in b for b in rt.blockers)


def test_ready_rc_session_not_blocked(tmp_path):
    base = str(tmp_path / "ready")
    seed_rc(base, "ready_with_warnings")
    rt = run_protocol(base)
    assert rt.session_status() in ("ready", "ready_with_warnings")
    assert not rt.blockers
