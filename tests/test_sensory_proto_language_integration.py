"""Sensory <-> Proto-language: input text is not an internal token directly."""

from __future__ import annotations

from solaris_ai_nn.sensory_membrane import (
    RawSensoryEvent,
    SensoryEventNormalizer,
    SensoryGroundingEngine,
    SensoryModality,
)


def test_text_input_does_not_become_internal_token_directly():
    eng = SensoryGroundingEngine(proto_symbol_threshold=3)
    norm = SensoryEventNormalizer()
    word = "thunder"
    for _ in range(4):
        eng.ground(norm.normalize(RawSensoryEvent(
            source_id="s", source_type="text_file",
            modality=SensoryModality.TEXTUAL, payload=word)))
    # A proto-symbol candidate exists, but it is NOT the raw input word.
    assert eng.proto_symbol_candidates
    for candidate in eng.proto_symbol_candidates:
        assert candidate != word
        assert candidate.startswith("env_sym::")


def test_internal_proto_symbol_candidate_generated():
    eng = SensoryGroundingEngine(proto_symbol_threshold=2)
    norm = SensoryEventNormalizer()
    for _ in range(3):
        eng.ground(norm.normalize(RawSensoryEvent(
            source_id="s", source_type="text_file", payload="rain")))
    ctx = eng.context()
    assert ctx["sensory_proto_symbol_candidates"]
    # The candidate is internally generated, distinct from human text.
    assert all(c.startswith("env_sym::")
               for c in ctx["sensory_proto_symbol_candidates"])


def test_single_occurrence_no_symbol():
    eng = SensoryGroundingEngine(proto_symbol_threshold=3)
    norm = SensoryEventNormalizer()
    eng.ground(norm.normalize(RawSensoryEvent(
        source_id="s", source_type="text_file", payload="once")))
    assert not eng.proto_symbol_candidates
