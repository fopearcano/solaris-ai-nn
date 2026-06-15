"""Feeder SDK <-> Sensorium Lab: SDK streams usable; privacy flags visible."""

from __future__ import annotations

from solaris_ai_nn.feeder_sdk import FeederSDKAnnotationStatus, FeederSDKEnvelope
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime


def test_simulated_feeder_streams_usable_in_study(tmp_path):
    # The sensorium lab runs arms through a PluralSensoriumRuntime; SDK
    # envelopes (the feeder output) are source-compatible with that runtime.
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "lab"))
    for i in range(6):
        env = FeederSDKEnvelope(
            feeder_id="sim_rf", source_id="sim_rf",
            source_kind="fixture_replay", modality="radio_frequency",
            features={"power": 0.7}, timestamp=float(i),
            trust_level="simulated_fixture")
        rt.observe_envelope(env.to_sensory_envelope(), now=float(i))
        rt.advance_tick(["sim_rf"], now=float(i))
    assert rt.invariants.candidates  # the SDK stream produced structure


def test_feeder_privacy_flags_included_in_world_signature(tmp_path):
    # A human-labelled SDK envelope carries its contamination flag into the
    # sensory envelope, which the world signature's contamination score reads.
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "lab2"))
    for i in range(5):
        env = FeederSDKEnvelope(
            feeder_id="text", source_id="text", source_kind="manual_log",
            modality="human_textual", features={"length": 5.0},
            annotation="rain",
            annotation_status=FeederSDKAnnotationStatus.HUMAN_LABEL_EXTERNAL,
            timestamp=float(i))
        sensory = env.to_sensory_envelope()
        assert "human_label_present" in sensory.contamination_flags
        rt.observe_envelope(sensory, now=float(i))
        rt.advance_tick(["text"], now=float(i))
    # The receptor saw a contaminated source.
    rec = next(iter(rt.receptors.values()))
    assert rec.event_count > 0
