"""Pilot-2 <-> proto-language / world model: source-marked, provenance-backed."""

from __future__ import annotations

from solaris_ai_nn.sensory_membrane import (
    RawSensoryEvent,
    SensoryEventNormalizer,
    SensoryGroundingEngine,
    SensoryModality,
)


def test_sensory_symbol_source_marked():
    eng = SensoryGroundingEngine(proto_symbol_threshold=2)
    norm = SensoryEventNormalizer()
    for _ in range(3):
        eng.ground(norm.normalize(RawSensoryEvent(
            source_id="weather", source_type="text_file",
            modality=SensoryModality.TEXTUAL, payload="rain")))
    # The candidate carries its source -> source-marked, internally generated.
    assert eng.proto_symbol_candidates
    assert "weather" in eng.proto_symbol_candidates[0]
    assert eng.proto_symbol_candidates[0].startswith("env_sym::")


def test_sensory_world_node_provenance_backed():
    eng = SensoryGroundingEngine()
    rec = eng.ground(SensoryEventNormalizer().normalize(
        RawSensoryEvent(source_id="s", source_type="jsonl_file",
                        payload={"x": 1}), provenance_refs=["prov1"]))
    assert rec.world_model_node_candidate == "env_source::s"
    assert "prov1" in rec.provenance_refs


def test_input_text_not_internal_token_directly():
    eng = SensoryGroundingEngine(proto_symbol_threshold=2)
    norm = SensoryEventNormalizer()
    for _ in range(3):
        eng.ground(norm.normalize(RawSensoryEvent(
            source_id="s", source_type="text_file", payload="thunder")))
    assert all(c != "thunder" for c in eng.proto_symbol_candidates)
