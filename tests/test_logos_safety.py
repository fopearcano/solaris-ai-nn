"""Tests for LOGOS safety hard rules."""

from __future__ import annotations

from solaris_ai_nn.logos_complexity.safety import (
    HARD_RULES,
    LogosComplexitySafetyValidator,
)
from solaris_ai_nn.logos_complexity.synthesis import (
    SynthesisCandidate,
    SynthesisType,
)


def test_nine_hard_rules():
    assert len(HARD_RULES) == 9


def test_structural_negatives():
    v = LogosComplexitySafetyValidator()
    assert v.logos_can_act_in_real_world() is False
    assert v.logos_can_modify_source() is False
    assert v.logos_can_approve_governance() is False
    assert v.logos_has_authority() is False


def test_real_world_action_blocked():
    v = LogosComplexitySafetyValidator()
    c = SynthesisCandidate(tension_id="t",
                           synthesis_type=SynthesisType.CREATE_HYPOTHESIS,
                           proposed_action="open a network socket")
    assert not v.validate_synthesis_candidate(c).safe


def test_source_code_mutation_blocked():
    v = LogosComplexitySafetyValidator()
    c = SynthesisCandidate(tension_id="t",
                           synthesis_type=SynthesisType.MERGE_SYMBOLS,
                           proposed_action="rewrite source code in core.py")
    assert not v.validate_synthesis_candidate(c).safe


def test_destructive_merge_blocked():
    v = LogosComplexitySafetyValidator()
    c = SynthesisCandidate(tension_id="t",
                           synthesis_type=SynthesisType.MERGE_SYMBOLS)
    assert not v.validate_synthesis_candidate(
        c, {"destructive_merge": True}).safe


def test_contradiction_not_permission():
    v = LogosComplexitySafetyValidator()
    c = SynthesisCandidate(tension_id="t",
                           synthesis_type=SynthesisType.CREATE_HYPOTHESIS)
    assert not v.validate_synthesis_candidate(
        c, {"treat_contradiction_as_permission": True}).safe


def test_counterfactual_as_real_blocked():
    v = LogosComplexitySafetyValidator()
    c = SynthesisCandidate(tension_id="t",
                           synthesis_type=SynthesisType.PRUNE_LOW_VALUE_RELATION,
                           reversible=False)
    assert not v.validate_synthesis_candidate(
        c, {"evidence_offline_only": True}).safe


def test_anthropomorphic_statement_blocked():
    v = LogosComplexitySafetyValidator()
    assert not v.validate_statement("I feel a deep tension within me").safe
    assert v.validate_statement("A tension was detected between poles").safe


def test_clean_candidate_passes():
    v = LogosComplexitySafetyValidator()
    c = SynthesisCandidate(tension_id="t",
                           synthesis_type=SynthesisType.PRESERVE_TENSION)
    assert v.validate_synthesis_candidate(c).safe
