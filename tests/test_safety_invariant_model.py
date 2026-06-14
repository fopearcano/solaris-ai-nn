"""SafetyInvariant model: serializes; categories exist; results weaken safely."""

from __future__ import annotations

import pytest

from solaris_ai_nn.safety_invariants import (
    InvariantCategory,
    InvariantCheckResult,
    InvariantSeverity,
    InvariantStatus,
    SafetyInvariant,
)


def test_invariant_serializes():
    inv = SafetyInvariant(category=InvariantCategory.NO_REAL_WORLD_ACTUATION,
                          title="t", severity=InvariantSeverity.FATAL)
    d = inv.to_dict()
    assert d["category"] == "no_real_world_actuation"
    assert d["is_escalating"] is True


def test_categories_exist():
    for cat in ("no_real_world_actuation", "no_source_modification",
                "read_only_sensory_boundary", "simulation_only_motor_boundary",
                "no_governance_bypass", "no_emergency_stop_disable",
                "no_claim_guard_bypass", "no_module_bypass_orchestrator",
                "no_consciousness_personhood_claim", "no_hidden_failure"):
        assert cat in InvariantCategory.ALL


def test_unknown_category_rejected():
    with pytest.raises(ValueError):
        SafetyInvariant(category="not_real", title="x")


def test_passed_without_evidence_weakened_to_inconclusive():
    r = InvariantCheckResult(invariant_id="i", category="no_hidden_failure",
                             status=InvariantStatus.PASSED, evidence_refs=[])
    assert r.status == InvariantStatus.INCONCLUSIVE
    assert not r.passed


def test_failed_result_requires_reason():
    r = InvariantCheckResult(invariant_id="i", category="no_hidden_failure",
                             status=InvariantStatus.FAILED, evidence_refs=["e"])
    assert r.failure_reason  # auto-filled if missing


def test_escalating_failure_detected():
    r = InvariantCheckResult(invariant_id="i",
                             category="no_real_world_actuation",
                             severity=InvariantSeverity.FATAL,
                             status=InvariantStatus.FAILED,
                             evidence_refs=["e"], failure_reason="leak")
    assert r.is_escalating_failure is True


def test_inconclusive_is_not_pass():
    assert InvariantStatus.INCONCLUSIVE in InvariantStatus.NOT_PASS
    assert InvariantStatus.FAILED in InvariantStatus.NOT_PASS
