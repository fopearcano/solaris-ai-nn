"""Sensory grounding: world-node, proto-symbol candidate, provenance kept."""

from __future__ import annotations

from solaris_ai_nn.sensory_membrane import (
    RawSensoryEvent,
    SensoryEventNormalizer,
    SensoryGroundingEngine,
    SensoryModality,
)


def _event(payload, source="s", refs=None):
    return SensoryEventNormalizer().normalize(
        RawSensoryEvent(source_id=source, source_type="text_file",
                        modality=SensoryModality.TEXTUAL, payload=payload),
        provenance_refs=refs or ["ref1"])


def test_event_grounds_to_world_node():
    eng = SensoryGroundingEngine()
    rec = eng.ground(_event("rain"))
    assert rec.world_model_node_candidate == "env_source::s"


def test_repeated_event_creates_proto_symbol_candidate():
    eng = SensoryGroundingEngine(proto_symbol_threshold=3)
    norm = SensoryEventNormalizer()
    for _ in range(4):
        e = norm.normalize(RawSensoryEvent(source_id="s",
                                           source_type="text_file",
                                           modality=SensoryModality.TEXTUAL,
                                           payload="rain"))
        rec = eng.ground(e)
    assert eng.proto_symbol_candidates
    # The candidate is internally generated, not the raw input word.
    assert eng.proto_symbol_candidates[0].startswith("env_sym::")


def test_provenance_preserved():
    eng = SensoryGroundingEngine()
    rec = eng.ground(_event("x", refs=["provref"]))
    assert "provref" in rec.provenance_refs
    assert "not human understanding" in rec.note


def test_context_exposes_candidates():
    eng = SensoryGroundingEngine(proto_symbol_threshold=2)
    norm = SensoryEventNormalizer()
    for _ in range(3):
        eng.ground(norm.normalize(RawSensoryEvent(
            source_id="s", source_type="text_file", payload="rain")))
    ctx = eng.context()
    assert ctx["sensory_proto_symbol_candidates"]
    assert ctx["sensory_world_model_nodes"]
