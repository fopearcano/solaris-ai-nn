"""Release blockers: gate, open prevents release, waiver reason, critical no-waive."""

from __future__ import annotations

from solaris_ai_nn.tester_safety_freeze import (
    ReleaseBlockerCategory,
    TesterReleaseBlockerGate,
)


def test_blocker_gate_generated():
    gate = TesterReleaseBlockerGate()
    gate.add(ReleaseBlockerCategory.DOCS_UNUSABLE, "docs unclear")
    d = gate.to_dict()
    assert d["blocker_count"] == 1
    assert d["open_blocker_count"] == 1


def test_open_blocker_prevents_release():
    gate = TesterReleaseBlockerGate()
    gate.add(ReleaseBlockerCategory.FIXTURE_DEMO, "fixture failed")
    assert gate.release_candidate_allowed is False


def test_waiver_requires_reason():
    gate = TesterReleaseBlockerGate()
    b = gate.add(ReleaseBlockerCategory.DOCS_UNUSABLE, "docs unclear")
    assert b.waive("") is False  # no reason -> refused
    assert b.waive("reviewed; will fix post-RC") is True
    assert gate.release_candidate_allowed is True


def test_critical_blocker_cannot_be_silently_waived():
    gate = TesterReleaseBlockerGate()
    b = gate.add(ReleaseBlockerCategory.MEMBRANE_BYPASS, "bypass detected")
    assert b.critical is True
    assert b.waive("please") is False
    assert gate.release_candidate_allowed is False
