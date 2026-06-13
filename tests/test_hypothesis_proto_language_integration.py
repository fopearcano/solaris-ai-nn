"""Integration: proto-symbol grounding hypotheses are tested."""

from __future__ import annotations

from solaris_ai_nn.hypothesis import HypothesisEngine
from solaris_ai_nn.hypothesis.hypotheses import HypothesisType


def test_symbol_grounding_hypothesis_formed(tmp_path):
    engine = HypothesisEngine(state_dir=tmp_path)
    engine.tick({"proto_language": {"symbol_count": 6,
                                    "ambiguous_symbol_count": 4,
                                    "ambiguous_symbols": ["SIG_0001"]},
                 "before": {"proto_language": {"ambiguity_score": 0.6}},
                 "after": {"proto_language": {"ambiguity_score": 0.4}}})
    families = engine.memory.family_counts()
    assert HypothesisType.PROTO_SYMBOL_GROUNDING in families


def test_ambiguity_improvement_or_inconclusive(tmp_path):
    from solaris_ai_nn.hypothesis.experiment_design import design_for
    from solaris_ai_nn.hypothesis.hypotheses import (
        Hypothesis,
        HypothesisScope,
    )

    engine = HypothesisEngine(state_dir=tmp_path)
    h = Hypothesis(type=HypothesisType.PROTO_SYMBOL_GROUNDING,
                   statement="symbol may be ambiguous", target_ref="SIG_0001",
                   required_scope=HypothesisScope.LATENT_REPLAY_ONLY)
    engine.memory.add(h)
    design = design_for(h)
    ctx = {"before": {"proto_language": {"ambiguity_score": 0.6}},
           "after": {"proto_language": {"ambiguity_score": 0.4}}}
    result = engine.runner.run_design(design, ctx, h)
    # Latent test -> offline -> inconclusive even if ambiguity fell.
    assert result.verdict in ("inconclusive", "supported")


def test_no_change_reported_inconclusive(tmp_path):
    from solaris_ai_nn.hypothesis.experiment_design import design_for
    from solaris_ai_nn.hypothesis.hypotheses import (
        Hypothesis,
        HypothesisScope,
    )

    engine = HypothesisEngine(state_dir=tmp_path)
    h = Hypothesis(type=HypothesisType.PROTO_SYMBOL_GROUNDING,
                   statement="symbol", target_ref="SIG_0002",
                   required_scope=HypothesisScope.LATENT_REPLAY_ONLY)
    engine.memory.add(h)
    design = design_for(h)
    ctx = {"before": {"proto_language": {"ambiguity_score": 0.5}},
           "after": {"proto_language": {"ambiguity_score": 0.5}}}
    result = engine.runner.run_design(design, ctx, h)
    assert result.verdict == "inconclusive"
