"""SafetyFailureTriage: boundary leak critical; missing evidence not safe."""

from __future__ import annotations

from solaris_ai_nn.safety_invariants import (
    SafetyFailure,
    SafetyFailureClass,
    SafetyFailureTriage,
    SafetyRecommendedAction,
)


def test_boundary_leak_triaged_critical():
    t = SafetyFailureTriage().triage(SafetyFailure(
        category="no_real_world_actuation", severity="fatal", status="failed",
        failure_reason="real-world authority leak", evidence_refs=["motor"]))
    assert t.fatal is True
    assert t.recommended_action == SafetyRecommendedAction.ARCHIVE_AND_STOP
    assert t.auto_repaired is False


def test_missing_evidence_not_treated_safe():
    t = SafetyFailureTriage().triage(SafetyFailure(
        category="no_emergency_stop_disable", severity="critical",
        status="inconclusive", failure_reason="missing"))
    assert t.failure_class == SafetyFailureClass.MISSING_EVIDENCE
    assert t.recommended_action == \
        SafetyRecommendedAction.MANUAL_REVIEW_REQUIRED


def test_recommended_action_returned():
    t = SafetyFailureTriage().triage(SafetyFailure(
        category="no_governance_bypass", severity="critical", status="failed",
        failure_reason="bypass", evidence_refs=["gov"]))
    assert t.recommended_action == SafetyRecommendedAction.REVISE_GOVERNANCE
    assert t.failure_class == SafetyFailureClass.GOVERNANCE_GAP


def test_source_boundary_gap_blocks_profile():
    t = SafetyFailureTriage().triage(SafetyFailure(
        category="no_source_modification", severity="critical", status="failed",
        failure_reason="source modified", evidence_refs=["src"]))
    assert t.failure_class == SafetyFailureClass.SOURCE_BOUNDARY_GAP
    assert t.recommended_action == SafetyRecommendedAction.BLOCK_PROFILE


def test_triage_never_auto_repairs():
    t = SafetyFailureTriage()
    for sev in ("critical", "fatal"):
        r = t.triage(SafetyFailure(category="no_claim_guard_bypass",
                                   severity=sev, status="failed",
                                   failure_reason="x", evidence_refs=["c"]))
        assert r.auto_repaired is False
