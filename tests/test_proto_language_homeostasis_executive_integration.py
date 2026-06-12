"""Tests for proto-language feeding homeostasis and the executive."""

from __future__ import annotations

from solaris_ai_nn.executive.coordinator import ExecutiveLayer
from solaris_ai_nn.homeostasis.desire_synthesis import DesireCandidate
from solaris_ai_nn.homeostasis.needs import NeedType
from solaris_ai_nn.homeostasis.regulation import HomeostaticRegulator
from solaris_ai_nn.protolanguage.layer import ProtoLanguageLayer


def test_symbol_ambiguity_increases_unknown_pressure():
    regulator = HomeostaticRegulator()
    result = regulator.update({"protolanguage": {
        "symbol_count": 10, "ambiguous_symbol_count": 8}})
    assert regulator.state.value("symbol_ambiguity_pressure") == 0.8
    need = result.need_state.by_type(NeedType.REDUCE_UNCERTAINTY)
    assert need is not None
    assert "symbol_ambiguity_pressure" in need.source_variables
    # Low ambiguity, low pressure.
    calm = HomeostaticRegulator()
    calm.update({"protolanguage": {"symbol_count": 10,
                                   "ambiguous_symbol_count": 1}})
    assert calm.state.value("symbol_ambiguity_pressure") == 0.1


def test_validated_symbol_supports_arbitration_without_override(tmp_path):
    layer = ProtoLanguageLayer(state_dir=tmp_path)
    layer.process_context({"repeated_actions": {"rest": 5}})
    symbol = layer.registry.find_by_type("action_symbol")[0]
    # Unvalidated: no support offered.
    assert layer.arbitration_support() == {}
    # Validate through measured prediction utility + stability.
    symbol.prediction_score = 0.6
    symbol.stability_score = 0.8
    symbol.ambiguity_score = 0.1
    symbol.observation_count = 6
    support = layer.arbitration_support()
    assert support["habit_support"]["rest"] > 0
    assert support["habit_support"]["rest"] <= 0.3  # capped small
    # Through the executive: support biases, governance still wins.
    executive = ExecutiveLayer()
    desires = [DesireCandidate(proposal="rest", motivation=0.6,
                               confidence=0.6)]
    blocked = executive.decide(
        desires, context={**support,
                          "governance_blocks":
                          {"rest": "operator pause"}}, step=1)
    scored = {s.candidate.label: s for s in blocked.scores}
    assert scored["rest"].blocked  # symbol support never overrides
    assert blocked.selected.label != "rest"


def test_supported_candidate_scores_higher_when_safe(tmp_path):
    layer = ProtoLanguageLayer(state_dir=tmp_path)
    layer.process_context({"repeated_actions": {"rest": 5}})
    symbol = layer.registry.find_by_type("action_symbol")[0]
    symbol.prediction_score = 0.6
    symbol.stability_score = 0.8
    symbol.observation_count = 6
    support = layer.arbitration_support()
    desires = [DesireCandidate(proposal="rest", motivation=0.5,
                               confidence=0.5)]
    plain = ExecutiveLayer().decide(desires, context={}, step=1)
    boosted = ExecutiveLayer().decide(desires, context=dict(support),
                                      step=1)
    plain_score = {s.candidate.label: s.total
                   for s in plain.scores}["rest"]
    boosted_score = {s.candidate.label: s.total
                     for s in boosted.scores}["rest"]
    assert boosted_score > plain_score  # a measured, small bias
    assert boosted.selected.committed is False
