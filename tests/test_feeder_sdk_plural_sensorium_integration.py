"""Feeder SDK <-> Plural Sensorium: envelope maps; modality; trust/privacy kept."""

from __future__ import annotations

from solaris_ai_nn.feeder_sdk import FeederSDKAnnotationStatus, FeederSDKEnvelope
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime
from solaris_ai_nn.plural_sensorium.event_envelope import SensoryEventEnvelope


def test_sdk_envelope_maps_to_sensory_envelope():
    env = FeederSDKEnvelope(
        feeder_id="rf", source_id="rf", source_kind="external_feature_drop",
        modality="radio_frequency", features={"power": 0.7})
    sensory = env.to_sensory_envelope()
    assert isinstance(sensory, SensoryEventEnvelope)


def test_modality_mapping_correct():
    for modality in ("radio_frequency", "ultrasound_echo", "vibration",
                     "magnetic", "human_textual"):
        env = FeederSDKEnvelope(feeder_id="f", source_id="s", source_kind="k",
                                modality=modality, features={"v": 0.5})
        assert env.to_sensory_envelope().modality == modality


def test_trust_and_privacy_flags_preserved():
    env = FeederSDKEnvelope(
        feeder_id="t", source_id="t", source_kind="manual_log",
        modality="human_textual", features={"length": 5.0},
        annotation="rain",
        annotation_status=FeederSDKAnnotationStatus.HUMAN_LABEL_EXTERNAL)
    sensory = env.to_sensory_envelope()
    # The human-label contamination flag carries into the sensory envelope.
    assert "human_label_present" in sensory.contamination_flags
    assert sensory.metadata.get("privacy_flags")
    assert sensory.metadata.get("schema_version")


def test_sdk_envelope_ingested_by_runtime():
    rt = PluralSensoriumRuntime(state_dir=".sann_feeders_test")
    env = FeederSDKEnvelope(
        feeder_id="rf", source_id="rf", source_kind="external_feature_drop",
        modality="radio_frequency", features={"power": 0.7}, timestamp=0.0)
    rt.observe_envelope(env.to_sensory_envelope(), now=0.0)
    rt.advance_tick(["rf"], now=0.0)
    assert rt.receptors
    assert "radio_frequency" in rt.active_modalities()
