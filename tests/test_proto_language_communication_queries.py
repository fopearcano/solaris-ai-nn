"""Tests for the proto-language communication queries."""

from __future__ import annotations

from solaris_ai_nn.governance.compliance import ClaimGuard
from solaris_ai_nn.protolanguage.layer import ProtoLanguageLayer
from solaris_ai_nn.protolanguage.reports import (
    HUMAN_LANGUAGE_ANSWER,
    ProtoLanguageQueryInterface,
)


def _queries(tmp_path):
    layer = ProtoLanguageLayer(state_dir=tmp_path)
    layer.process_context({
        "repeated_stimulus_patterns": {"light_noise": 5},
        "absence_states": {"silence": 4}})
    tokens = [s.token for s in layer.registry.symbols.values()]
    layer.utterances.build(tokens[:2], purpose="explanation")
    return layer, ProtoLanguageQueryInterface(layer)


def test_emerged_symbols_query_grounded(tmp_path):
    layer, queries = _queries(tmp_path)
    result = queries.answer("what symbols emerged?")
    assert result.answered
    assert "internally generated symbol" in result.text
    assert "grounded in recorded evidence" in result.text
    token = list(layer.registry.symbols.values())[0].token
    assert token in result.text


def test_symbol_meaning_query(tmp_path):
    layer, queries = _queries(tmp_path)
    token = list(layer.registry.symbols.values())[0].token
    result = queries.answer("what does this symbol mean?", token=token)
    assert "grounded in" in result.text
    assert "not human understanding" in result.text
    missing = queries.answer("what does this symbol mean?",
                             token="GHOST_0001")
    assert "No symbol" in missing.text


def test_human_language_query_safe_answer(tmp_path):
    _, queries = _queries(tmp_path)
    result = queries.answer("is this human language?")
    assert result.text == HUMAN_LANGUAGE_ANSWER
    assert result.text.startswith("No.")
    assert "not human language" in result.text


def test_all_seven_queries_supported_and_safe(tmp_path):
    _, queries = _queries(tmp_path)
    assert len(queries.supported_queries()) == 7
    guard = ClaimGuard()
    for question in queries.supported_queries():
        answer = queries.answer(question)
        assert guard.is_safe(answer.text), question
        lowered = answer.text.lower()
        for forbidden in ("i want", "i feel", "is conscious",
                          "speaks english", "understands like a human"):
            assert forbidden not in lowered, (question, forbidden)


def test_prediction_query_honest_and_unknown_fallback(tmp_path):
    _, queries = _queries(tmp_path)
    prediction = queries.answer("did symbols improve prediction?")
    assert "no evidence either way" in prediction.text.lower() \
        or "did not improve" in prediction.text.lower() \
        or "improvement" in prediction.text.lower()
    unknown = queries.answer("can the symbols dream?")
    assert not unknown.answered
