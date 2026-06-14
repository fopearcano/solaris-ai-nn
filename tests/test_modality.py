"""Sensory modality: modalities exist; camera/audio are metadata-only."""

from __future__ import annotations

from solaris_ai_nn.sensory_membrane import (
    ModalitySignal,
    SensoryModality,
    classify_modality,
)


def test_modalities_exist():
    for m in ("textual", "numeric", "file_presence", "file_change",
              "temporal", "simulated_visual", "simulated_audio",
              "environmental_event", "unknown"):
        assert m in SensoryModality.ALL


def test_simulated_camera_audio_metadata_only():
    cam = classify_modality("simulated_camera_metadata")
    aud = classify_modality("simulated_audio_metadata")
    assert cam.modality == SensoryModality.SIMULATED_VISUAL
    assert aud.modality == SensoryModality.SIMULATED_AUDIO
    assert cam.metadata_only and aud.metadata_only
    assert any("no image" in n.lower() or "metadata" in n.lower()
               for n in cam.notes)


def test_classify_text_and_numeric():
    assert classify_modality("text_file").modality == SensoryModality.TEXTUAL
    assert classify_modality("numeric_csv").modality == SensoryModality.NUMERIC


def test_hint_overrides():
    sig = classify_modality("jsonl_file", hint="numeric")
    assert sig.modality == SensoryModality.NUMERIC


def test_signal_normalizes_unknown():
    sig = ModalitySignal(modality="not_a_modality")
    assert sig.modality == SensoryModality.UNKNOWN
