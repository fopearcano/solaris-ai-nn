"""Sensory <-> World model: source/provenance/pattern nodes (as candidates)."""

from __future__ import annotations

from solaris_ai_nn.sensory_membrane import (
    RawSensoryEvent,
    SensoryEventNormalizer,
    SensoryGroundingEngine,
    SensoryModality,
)


def test_source_node_created():
    eng = SensoryGroundingEngine()
    rec = eng.ground(SensoryEventNormalizer().normalize(
        RawSensoryEvent(source_id="weather", source_type="numeric_csv",
                        modality=SensoryModality.NUMERIC,
                        numeric_values={"value": 1.0})))
    assert rec.world_model_node_candidate == "env_source::weather"


def test_provenance_node_preserved():
    eng = SensoryGroundingEngine()
    rec = eng.ground(SensoryEventNormalizer().normalize(
        RawSensoryEvent(source_id="s", source_type="jsonl_file",
                        payload={"x": 1}), provenance_refs=["provref"]))
    assert "provref" in rec.provenance_refs


def test_event_pattern_node_via_context():
    eng = SensoryGroundingEngine(proto_symbol_threshold=2)
    norm = SensoryEventNormalizer()
    for _ in range(3):
        eng.ground(norm.normalize(RawSensoryEvent(
            source_id="s", source_type="folder_poll",
            modality=SensoryModality.FILE_CHANGE, payload="a.txt")))
    ctx = eng.context()
    assert ctx["sensory_world_model_nodes"]
    # Recurring pattern produced a hypothesis seed (recurring::...).
    assert any("recurring" in s for s in ctx["sensory_hypothesis_seeds"])


def test_source_metadata_is_provenance_not_truth():
    raw = RawSensoryEvent(source_id="s", source_type="text_file",
                          payload="the sky is green")
    stim = SensoryEventNormalizer().normalize(raw).to_stimulus_dict()
    # The text is environmental content, not a truth label or command.
    assert stim["origin"] == "read_only_environmental_input"
    assert stim["executable_scope"] == "none"
