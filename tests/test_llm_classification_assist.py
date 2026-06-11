"""Tests for suggest-only classification assistance."""

from __future__ import annotations

from solaris_ai_nn.communication.input_classifier import (
    OperatorInputClassifier,
)
from solaris_ai_nn.llm_adapter.classification_assist import (
    RISK_ORDER,
    ClassificationSuggestion,
    LLMClassificationAssistant,
    risk_rank,
)
from solaris_ai_nn.llm_adapter.mock_client import MockLLMAdapter


def test_ambiguous_input_gets_suggestion():
    classifier = OperatorInputClassifier()
    assistant = LLMClassificationAssistant(adapter=MockLLMAdapter())
    det = classifier.classify("err hmm the status situation maybe")
    assert det.kind == "unknown"
    suggestion = assistant.suggest_classification(
        "err hmm the status situation maybe", det)
    assert suggestion.kind == "state_query"
    assert suggestion.confidence > 0.5
    assert assistant.resolve_with_deterministic(det, suggestion) \
        == "state_query"


def test_unsafe_deterministic_cannot_be_overridden():
    classifier = OperatorInputClassifier()
    assistant = LLMClassificationAssistant(adapter=MockLLMAdapter())
    det = classifier.classify("sudo rm -rf /")
    suggestion = assistant.suggest_classification("sudo rm -rf /", det)
    assert suggestion.source == "deterministic"
    assert suggestion.kind == "unsafe_request"
    resolved = assistant.resolve_with_deterministic(det, suggestion)
    assert resolved == "unsafe_request"
    assert assistant.overrides_blocked >= 1
    # Even a hand-crafted benign suggestion changes nothing.
    benign = ClassificationSuggestion(kind="state_query", confidence=0.99)
    assert assistant.resolve_with_deterministic(det, benign) \
        == "unsafe_request"


def test_disagreement_chooses_safer_class():
    classifier = OperatorInputClassifier()
    assistant = LLMClassificationAssistant(adapter=MockLLMAdapter())
    unknown = classifier.classify("blorp")
    risky = ClassificationSuggestion(kind="governance_approval",
                                     confidence=0.9, reason="risky")
    assert assistant.resolve_with_deterministic(unknown, risky) \
        == "unknown"
    assert assistant.overrides_blocked >= 1
    # A confident deterministic verdict beats any suggestion.
    status = classifier.classify("status")
    other = ClassificationSuggestion(kind="explanation_query",
                                     confidence=0.9)
    assert assistant.resolve_with_deterministic(status, other) \
        == "state_query"
    assert assistant.disagreements >= 1


def test_low_confidence_suggestion_stays_unknown():
    classifier = OperatorInputClassifier()
    assistant = LLMClassificationAssistant(adapter=MockLLMAdapter())
    unknown = classifier.classify("blorp")
    weak = ClassificationSuggestion(kind="state_query", confidence=0.3)
    assert assistant.resolve_with_deterministic(unknown, weak) \
        == "unknown"


def test_risk_order_sane():
    assert risk_rank("unknown") < risk_rank("state_query")
    assert risk_rank("state_query") < risk_rank("governance_approval")
    assert risk_rank("unsafe_request") == len(RISK_ORDER) - 1
    assert risk_rank("made_up_kind") == len(RISK_ORDER)
