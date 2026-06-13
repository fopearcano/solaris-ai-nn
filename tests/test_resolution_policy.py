"""Tests for the LOGOS resolution policy."""

from __future__ import annotations

from solaris_ai_nn.logos_complexity.resolution_policy import (
    ResolutionMode,
    ResolutionPolicy,
)
from solaris_ai_nn.logos_complexity.synthesis import SynthesisEngine
from solaris_ai_nn.logos_complexity.tension import (
    LogosTension,
    TensionPolarity,
    TensionType,
)


def _tension(ttype, pa=TensionPolarity.SUPPORT, pb=TensionPolarity.CONTRADICTION):
    return LogosTension(tension_type=ttype, polarity_a=pa, polarity_b=pb,
                        evidence_refs=["e"])


def _candidates(tension):
    return SynthesisEngine().propose(tension, {})


def test_balanced_mode_chooses_safe_candidate():
    policy = ResolutionPolicy(mode=ResolutionMode.BALANCED_RESOLUTION)
    tension = _tension(TensionType.SYMBOL_AMBIGUITY,
                       TensionPolarity.STABLE, TensionPolarity.AMBIGUOUS)
    decision = policy.decide(tension, _candidates(tension), {})
    assert decision.candidate is not None


def test_emergency_blocks_speculative_synthesis():
    policy = ResolutionPolicy(mode=ResolutionMode.SYNTHESIS_PREFERRED)
    tension = _tension(TensionType.WORLD_MODEL_CONTRADICTION)
    decision = policy.decide(tension, _candidates(tension),
                             {"emergency": True})
    assert decision.mode == ResolutionMode.EMERGENCY_STABILIZATION
    if decision.candidate is not None and decision.apply_allowed:
        assert decision.candidate.synthesis_type in (
            "stabilize_executive_policy", "request_auto_regeneration",
            "request_memory_consolidation", "preserve_tension",
            "no_synthesis")


def test_safety_tension_dominates_curiosity():
    policy = ResolutionPolicy(mode=ResolutionMode.SYNTHESIS_PREFERRED)
    tension = _tension(TensionType.NEED_SAFETY, TensionPolarity.NEED,
                       TensionPolarity.SAFETY)
    decision = policy.decide(tension, _candidates(tension), {})
    assert decision.preserve is True


def test_observe_only_preserves():
    policy = ResolutionPolicy(mode=ResolutionMode.OBSERVE_ONLY)
    tension = _tension(TensionType.SYMBOL_AMBIGUITY)
    decision = policy.decide(tension, _candidates(tension), {})
    assert decision.preserve is True


def test_ambiguity_routes_to_sampling():
    policy = ResolutionPolicy(mode=ResolutionMode.BALANCED_RESOLUTION)
    tension = _tension(TensionType.SYMBOL_AMBIGUITY,
                       TensionPolarity.STABLE, TensionPolarity.AMBIGUOUS)
    decision = policy.decide(tension, _candidates(tension), {})
    assert decision.candidate.synthesis_type == "request_active_sampling"
