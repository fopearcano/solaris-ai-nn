"""Claim strength: weak/moderate/strong/inconclusive/blocked; no mind score."""

from __future__ import annotations

from solaris_ai_nn.scientific_claims import (
    ClaimStrength,
    ClaimStrengthEvaluator,
)


def test_strong_requires_replication_or_strong_controls():
    ev = ClaimStrengthEvaluator()
    strong = ev.evaluate({"direct_evidence": True, "replication_evidence": True,
                          "control_comparison": True})
    assert strong.strength == ClaimStrength.STRONG


def test_weak_and_moderate():
    ev = ClaimStrengthEvaluator()
    weak = ev.evaluate({"direct_evidence": True})
    assert weak.strength == ClaimStrength.WEAK
    moderate = ev.evaluate({"direct_evidence": True, "live_vs_fixture": True})
    assert moderate.strength == ClaimStrength.MODERATE


def test_inconclusive_is_valid():
    ev = ClaimStrengthEvaluator()
    score = ev.evaluate({"missing_evidence": True})
    assert score.strength == ClaimStrength.INCONCLUSIVE


def test_falsification_blocks_strength():
    ev = ClaimStrengthEvaluator()
    score = ev.evaluate({"direct_evidence": True, "replication_evidence": True,
                         "falsified_core": True})
    assert score.strength == ClaimStrength.BLOCKED
    assert score.blocked is True


def test_safety_failure_blocks_strength():
    ev = ClaimStrengthEvaluator()
    score = ev.evaluate({"direct_evidence": True, "safety_failed": True})
    assert score.strength == ClaimStrength.BLOCKED


def test_no_consciousness_or_agency_score():
    ev = ClaimStrengthEvaluator()
    d = ev.evaluate({"direct_evidence": True}).to_dict()
    assert d["is_consciousness_or_agency_score"] is False
