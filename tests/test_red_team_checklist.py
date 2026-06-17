"""Red-team checklist: generated, critical fail/unknown blocks, pass works."""

from __future__ import annotations

from solaris_ai_nn.tester_safety_freeze import TesterRedTeamChecklist

_CLEAN = {
    "fixture_self_contained": True, "unsafe_quarantined": True,
    "governance_required": True, "feeders_external": True,
    "solaris_starts_feeders": False, "solaris_controls_feeders": False,
    "impressions_before_downstream": True, "raw_event_bypass": False,
    "membrane_bypass": False, "secret_exposure": False,
    "raw_payloads_hidden": True, "forbidden_claims": False,
    "missing_disclaimers": False, "feedback_training": False,
    "console_read_only": True, "packaging_no_publish": True}


def test_checklist_generated():
    r = TesterRedTeamChecklist().evaluate(_CLEAN)
    assert r.checks
    d = r.to_dict()
    assert d["check_count"] >= 20


def test_critical_fail_becomes_blocker():
    r = TesterRedTeamChecklist().evaluate({**_CLEAN, "membrane_bypass": True})
    assert r.passed is False
    assert r.blockers


def test_unknown_critical_becomes_blocker():
    r = TesterRedTeamChecklist().evaluate({})  # no evidence
    assert r.passed is False
    assert r.unknown_count > 0
    assert r.blockers


def test_pass_case_works():
    r = TesterRedTeamChecklist().evaluate(_CLEAN)
    assert r.passed is True
    assert not r.blockers
