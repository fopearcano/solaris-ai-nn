"""Integration: latent-replay tests produce offline evidence."""

from __future__ import annotations

from solaris_ai_nn.hypothesis import HypothesisEngine
from solaris_ai_nn.hypothesis.evidence import EvidenceType
from solaris_ai_nn.hypothesis.experiment_design import design_for
from solaris_ai_nn.hypothesis.hypotheses import (
    Hypothesis,
    HypothesisScope,
    HypothesisType,
)


def test_latent_replay_test_is_offline(tmp_path):
    engine = HypothesisEngine(state_dir=tmp_path)
    h = Hypothesis(type=HypothesisType.MYSTERIUM_REDUCTION,
                   statement="sampling may reduce unknown pressure",
                   target_ref="unknown",
                   required_scope=HypothesisScope.LATENT_REPLAY_ONLY)
    engine.memory.add(h)
    design = design_for(h)
    ctx = {"mysterium_pressure": 0.8,
           "after": {"mysterium_pressure": 0.5}}
    result = engine.runner.run_design(design, ctx, h)
    assert result.scope == "latent_replay"
    # Even though the metric improved, latent evidence stays offline and
    # cannot fully promote -> the verdict is inconclusive.
    assert result.verdict == "inconclusive"
    ev = engine.runner.evidence_ledger.records[-1]
    assert ev.is_offline is True


def test_counterfactual_evidence_not_real(tmp_path):
    engine = HypothesisEngine(state_dir=tmp_path)
    from solaris_ai_nn.hypothesis.evidence import EvidenceRecord

    rec = EvidenceRecord(
        hypothesis_id="h", evidence_type=EvidenceType.LATENT_REPLAY,
        source_scope="latent_replay",
        observation="counterfactual replay was consistent")
    assert rec.is_offline is True
    assert any("offline" in lim.lower() for lim in rec.limitations)
