"""Integration: LOGOS tensions and active perception."""

from __future__ import annotations

from solaris_ai_nn.active_perception import (
    ActiveSensingController,
    ExplorationMemory,
    SamplingPolicy,
)
from solaris_ai_nn.logos_complexity import LogosComplexityEngine, ResolutionPolicy
from solaris_ai_nn.logos_complexity.synthesis import (
    SynthesisCandidate,
    SynthesisEngine,
    SynthesisType,
)
from solaris_ai_nn.logos_complexity.tension import (
    LogosTension,
    TensionPolarity,
    TensionType,
)


def test_tension_requests_sampling():
    t = LogosTension(tension_type=TensionType.SYMBOL_AMBIGUITY,
                     polarity_a=TensionPolarity.STABLE,
                     polarity_b=TensionPolarity.AMBIGUOUS,
                     related_symbols=["ABS_0001"], evidence_refs=["e"])
    candidates = SynthesisEngine().propose(t, {})
    assert any(c.synthesis_type == SynthesisType.REQUEST_ACTIVE_SAMPLING
               for c in candidates)


def test_active_perception_safety_still_applies(tmp_path):
    controller = ActiveSensingController(
        policy=SamplingPolicy(mode="balanced", seed=7),
        memory=ExplorationMemory(state_dir=tmp_path))
    engine = LogosComplexityEngine(
        state_dir=tmp_path,
        policy=ResolutionPolicy(mode="balanced_resolution"),
        active_perception=controller)
    engine.tick({"proto_language": {"symbol_count": 10,
                                    "ambiguous_symbol_count": 6,
                                    "ambiguous_symbols": ["ABS_0001"]}})
    # Active perception's own safety is unchanged and authoritative.
    assert controller.safety.sampling_can_act_in_real_world() is False


def test_sampling_request_applied_only_with_controller(tmp_path):
    engine_no_ap = SynthesisEngine()
    candidate = SynthesisCandidate(
        tension_id="t", synthesis_type=SynthesisType.REQUEST_ACTIVE_SAMPLING)
    result = engine_no_ap.apply_if_allowed(candidate, {})
    # Without an attached controller, the request is recorded but not applied.
    assert result.applied is False
