"""Sensory event normalizer: canonical stimulus, absence, provenance."""

from __future__ import annotations

from solaris_ai_nn.sensory_membrane import (
    RawSensoryEvent,
    SensoryEventNormalizer,
    SensoryModality,
)


def test_raw_event_normalizes():
    raw = RawSensoryEvent(source_id="s", source_type="text_file",
                          modality=SensoryModality.TEXTUAL, payload="hello")
    norm = SensoryEventNormalizer().normalize(raw)
    assert norm.source_id == "s"
    assert 0.0 <= norm.intensity <= 1.0
    assert "not_operator_command" in norm.safety_tags


def test_absence_event_generated():
    norm = SensoryEventNormalizer().absence_event("s", "text_file")
    assert norm.is_absence is True
    stim = norm.to_stimulus_dict()
    assert stim["is_absence"] is True


def test_canonical_stimulus_emitted():
    raw = RawSensoryEvent(source_id="s", source_type="jsonl_file",
                          modality=SensoryModality.ENVIRONMENTAL_EVENT,
                          payload={"x": 1})
    stim = SensoryEventNormalizer().normalize(raw).to_stimulus_dict()
    assert stim["kind"] == "Stimulus"
    assert stim["origin"] == "read_only_environmental_input"
    assert stim["executable_scope"] == "none"


def test_provenance_attached():
    raw = RawSensoryEvent(source_id="s", source_type="text_file",
                          payload="x")
    norm = SensoryEventNormalizer().normalize(raw, provenance_refs=["ref1"])
    assert norm.provenance_refs == ["ref1"]


def test_external_valence_is_hint_not_outcome():
    raw = RawSensoryEvent(source_id="s", source_type="jsonl_file",
                          payload={}, external_valence_hint=0.5)
    hint = SensoryEventNormalizer().normalize(raw).to_reaction_hint_dict()
    assert hint is not None
    assert hint["is_system_outcome"] is False
    assert hint["origin"] == "external_environment_hint"


def test_novelty_decays_with_recurrence():
    norm = SensoryEventNormalizer()
    first = norm.normalize(RawSensoryEvent(source_id="s",
                                           source_type="text_file",
                                           payload="same"))
    second = norm.normalize(RawSensoryEvent(source_id="s",
                                            source_type="text_file",
                                            payload="same"))
    assert second.novelty < first.novelty
