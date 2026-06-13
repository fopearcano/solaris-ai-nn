"""Integration: LOGOS routes to latent replay and auto-regeneration."""

from __future__ import annotations

from solaris_ai_nn.logos_complexity.synthesis import (
    SynthesisEngine,
    SynthesisType,
)
from solaris_ai_nn.logos_complexity.tension import (
    LogosTension,
    TensionPolarity,
    TensionType,
)


def _tension(ttype, pa, pb):
    return LogosTension(tension_type=ttype, polarity_a=pa, polarity_b=pb,
                        evidence_refs=["e"])


def test_unresolved_tension_requests_replay():
    t = _tension(TensionType.MYSTERIUM_SYNTHESIS, TensionPolarity.MYSTERIUM,
                 TensionPolarity.SYNTHESIS)
    candidates = SynthesisEngine().propose(t, {})
    assert any(c.synthesis_type == SynthesisType.REQUEST_LATENT_REPLAY
               for c in candidates)


def test_overload_requests_diagnostics():
    t = _tension(TensionType.COMPLEXITY_OVERLOAD, TensionPolarity.COMPLEX,
                 TensionPolarity.SIMPLE)
    candidates = SynthesisEngine().propose(t, {})
    assert any(c.synthesis_type == SynthesisType.REQUEST_AUTO_REGENERATION
               for c in candidates)


def test_latent_replay_request_is_offline():
    engine = SynthesisEngine()
    from solaris_ai_nn.logos_complexity.synthesis import SynthesisCandidate

    candidate = SynthesisCandidate(
        tension_id="t", synthesis_type=SynthesisType.REQUEST_LATENT_REPLAY)
    result = engine.apply_if_allowed(candidate, {})
    assert "offline" in result.detail.lower()
