"""RC readiness gate: ready, warnings, blocked by packaging/safety/claim/membrane."""

from __future__ import annotations

from solaris_ai_nn.tester_release_candidate import TesterRCReadinessGate

_OK_PKG = {"packaging_available": True, "doctor_status": "pass",
           "clean_machine_readiness": "pass"}
_OK_SF = {"safety_freeze_available": True, "readiness": "ready"}
_OK_FIX = {"fixture_demo_available": True, "fixture_passed": True}


def _base(**over):
    ctx = {"packaging": _OK_PKG, "safety_freeze": _OK_SF, "fixture": _OK_FIX,
           "artifacts": {"missing_required": []}}
    ctx.update(over)
    return ctx


def test_ready_case():
    r = TesterRCReadinessGate().evaluate(_base())
    assert r.status == "ready"
    assert not r.blockers


def test_ready_with_warnings_case():
    r = TesterRCReadinessGate().evaluate(_base(
        artifacts={"missing_required": [],
                   "missing_recommended": ["membrane_report"]}))
    assert r.status == "ready_with_warnings"
    assert r.warnings


def test_blocked_by_packaging():
    r = TesterRCReadinessGate().evaluate(_base(
        packaging={"packaging_available": False}))
    assert r.status in ("blocked", "critical_blocked")


def test_blocked_by_safety_freeze():
    r = TesterRCReadinessGate().evaluate(_base(
        safety_freeze={"safety_freeze_available": True,
                       "readiness": "blocked",
                       "open_release_blocker_count": 1}))
    assert r.status in ("blocked", "critical_blocked")


def test_blocked_by_forbidden_claim():
    r = TesterRCReadinessGate().evaluate(_base(
        safety_freeze={"safety_freeze_available": True, "readiness": "ready",
                       "forbidden_claim_count": 2}))
    assert r.status == "critical_blocked"
    assert r.critical_blockers


def test_blocked_by_missing_membrane():
    r = TesterRCReadinessGate().evaluate(_base(
        membrane={"live_modules_ran": True, "present": False}))
    assert r.status == "critical_blocked"


def test_waiver_of_non_critical(tmp_path):
    gate = TesterRCReadinessGate(waived_blockers=["clean_machine_readiness"])
    r = gate.evaluate(_base(
        packaging={"packaging_available": True, "doctor_status": "pass",
                   "clean_machine_readiness": "fail"}))
    # The waived non-critical blocker becomes a warning, not a blocker.
    assert all(b.check != "clean_machine_readiness" for b in r.blockers)
