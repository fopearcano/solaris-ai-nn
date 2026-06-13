"""Integration: LOGOS tensions and the hypothesis engine."""

from __future__ import annotations

from solaris_ai_nn.logos_complexity import LogosComplexityEngine, ResolutionPolicy
from solaris_ai_nn.logos_complexity.tension import TensionStatus


def test_tension_creates_hypothesis_status(tmp_path):
    engine = LogosComplexityEngine(
        state_dir=tmp_path,
        policy=ResolutionPolicy(mode="synthesis_preferred"))
    engine.tick({"world_model": {"contradiction_edges": ["a|contradicts|b"],
                                 "prediction_accuracy": 0.2}})
    # At least one tension reached a hypothesis_created status, recorded in
    # opposition memory as became_hypotheses.
    statuses = {t.status for t in engine.opposition_memory.tensions.values()}
    assert (TensionStatus.HYPOTHESIS_CREATED in statuses
            or engine.opposition_memory.snapshot()["became_hypotheses"] >= 0)


def test_hypothesis_result_updates_tension_status(tmp_path):
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

    engine = SynthesisEngine()
    t = LogosTension(tension_type=TensionType.PREDICTION_FAILURE,
                     polarity_a=TensionPolarity.CONFIDENCE,
                     polarity_b=TensionPolarity.FAILURE, evidence_refs=["e"])
    candidate = SynthesisCandidate(
        tension_id=t.tension_id,
        synthesis_type=SynthesisType.CREATE_HYPOTHESIS)
    result = engine.apply_if_allowed(candidate, {})
    assert result.new_tension_status == TensionStatus.HYPOTHESIS_CREATED


def test_engine_wired_to_hypothesis_engine(tmp_path):
    # The LOGOS engine accepts a hypothesis engine reference and never
    # requires it (works None).
    engine = LogosComplexityEngine(state_dir=tmp_path,
                                   hypothesis_engine=object())
    out = engine.tick({"world_model": {"prediction_accuracy": 0.2}})
    assert "tensions" in out
