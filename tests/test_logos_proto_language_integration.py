"""Integration: proto-symbol ambiguity feeds LOGOS tension."""

from __future__ import annotations

from solaris_ai_nn.logos_complexity import LogosComplexityEngine
from solaris_ai_nn.logos_complexity.synthesis import (
    SynthesisEngine,
    SynthesisType,
)
from solaris_ai_nn.logos_complexity.tension import (
    LogosTension,
    TensionPolarity,
    TensionType,
)


def test_ambiguous_symbol_feeds_tension(tmp_path):
    engine = LogosComplexityEngine(state_dir=tmp_path)
    engine.tick({"proto_language": {"symbol_count": 10,
                                    "ambiguous_symbol_count": 6,
                                    "ambiguous_symbols": ["ABS_0001"]}})
    by_type = engine.fracture.snapshot()["by_type"]
    assert by_type.get(TensionType.SYMBOL_AMBIGUITY, 0) >= 1


def test_split_or_merge_candidate_proposed_safely():
    t = LogosTension(tension_type=TensionType.SYMBOL_AMBIGUITY,
                     polarity_a=TensionPolarity.STABLE,
                     polarity_b=TensionPolarity.AMBIGUOUS,
                     related_symbols=["ABS_0001"], evidence_refs=["e"])
    candidates = SynthesisEngine().propose(t, {})
    types = {c.synthesis_type for c in candidates}
    assert (SynthesisType.SPLIT_SYMBOL in types
            or SynthesisType.REQUEST_ACTIVE_SAMPLING in types
            or SynthesisType.MARK_AMBIGUOUS in types)


def test_symbols_never_renamed():
    # No synthesis type renames a symbol with a human word; the available
    # operations are split / merge / mark / request-disambiguation only.
    assert "rename_symbol" not in SynthesisType.ALL
