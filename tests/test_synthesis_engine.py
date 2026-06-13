"""Tests for the LOGOS synthesis engine."""

from __future__ import annotations

from solaris_ai_nn.logos_complexity.synthesis import (
    SynthesisEngine,
    SynthesisType,
    synthesis_to_candidate,
)
from solaris_ai_nn.logos_complexity.tension import (
    LogosTension,
    TensionPolarity,
    TensionType,
)


def _tension(ttype=TensionType.SYMBOL_AMBIGUITY):
    return LogosTension(tension_type=ttype,
                        polarity_a=TensionPolarity.STABLE,
                        polarity_b=TensionPolarity.AMBIGUOUS,
                        evidence_refs=["e"])


def test_proposes_candidates():
    engine = SynthesisEngine()
    candidates = engine.propose(_tension(), {})
    assert candidates
    assert all(c.synthesis_type in SynthesisType.ALL for c in candidates)


def test_preserves_unresolved_tension():
    engine = SynthesisEngine()
    candidates = engine.propose(_tension(TensionType.NEED_SAFETY), {})
    assert any(c.synthesis_type == SynthesisType.PRESERVE_TENSION
               for c in candidates)


def test_unsafe_synthesis_refused():
    engine = SynthesisEngine()
    candidates = engine.propose(_tension(), {})
    candidate = candidates[0]
    result = engine.apply_if_allowed(
        candidate, {"treat_contradiction_as_permission": True})
    assert result.refused is True


def test_apply_preserve_tension():
    engine = SynthesisEngine()
    candidates = engine.propose(_tension(TensionType.KNOWN_UNKNOWN), {})
    preserve = next(c for c in candidates
                    if c.synthesis_type == SynthesisType.PRESERVE_TENSION)
    result = engine.apply_if_allowed(preserve, {})
    assert result.applied is True
    assert result.result_class == "preserved"


def test_select_prefers_low_risk_reversible():
    engine = SynthesisEngine()
    candidates = engine.propose(_tension(TensionType.SYMBOL_AMBIGUITY), {})
    best = engine.select_candidate(candidates, {})
    assert best is not None


def test_synthesis_to_candidate_is_suggestion():
    engine = SynthesisEngine()
    candidate = engine.propose(_tension(TensionType.PREDICTION_FAILURE),
                               {})[0]
    cand = synthesis_to_candidate(candidate)
    assert cand.committed is False
