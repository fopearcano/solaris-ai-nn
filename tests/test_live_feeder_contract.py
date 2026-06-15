"""LiveFeederContract / envelope: serializes; provenance; read-only required."""

from __future__ import annotations

from solaris_ai_nn.live_field import (
    LiveFeederContract,
    LiveFeederEnvelope,
    LiveFeederMode,
)


def test_envelope_serializes():
    env = LiveFeederEnvelope(
        source_id="rf", feeder_id="rf_feed",
        feeder_mode=LiveFeederMode.EXTERNAL_FEATURE_DROP,
        modality="radio_frequency", features={"power": 0.7})
    data = env.to_dict()
    assert data["modality"] == "radio_frequency"
    assert data["feeder_id"] == "rf_feed"
    rebuilt = LiveFeederEnvelope.from_dict(data)
    assert rebuilt.source_id == "rf"


def test_provenance_required():
    env = LiveFeederEnvelope(
        source_id="rf", feeder_id="rf_feed", feeder_mode="local_file",
        modality="radio_frequency", features={"p": 1.0})
    assert env.has_provenance
    assert env.provenance["source_id"] == "rf"
    assert env.provenance["feeder_id"] == "rf_feed"


def test_read_only_true_required():
    env = LiveFeederEnvelope(
        source_id="x", feeder_id="f", feeder_mode="manual",
        modality="human_textual", features={}, read_only=False)
    assert env.read_only is True
    assert env.to_dict()["read_only"] is True


def test_source_mutable_false_required():
    env = LiveFeederEnvelope(
        source_id="x", feeder_id="f", feeder_mode="manual",
        modality="human_textual", features={}, source_mutable_by_solaris=True)
    assert env.source_mutable_by_solaris is False


def test_contract_builds_envelope():
    contract = LiveFeederContract()
    env = contract.build_envelope(
        {"modality": "alien_rf", "power": 0.7, "ts": 1.0},
        feeder_id="rf_feed", feeder_mode=LiveFeederMode.LOCAL_FILE,
        source_id="rf", modality_hint="alien_rf")
    assert env.modality == "radio_frequency"
    assert env.features["power"] == 0.7
    # The plural-sensorium envelope is compatible.
    sensory = env.to_sensory_envelope()
    assert sensory.modality == "radio_frequency"
    assert sensory.read_only is True


def test_executable_payload_rejected():
    contract = LiveFeederContract()
    ok, why = contract.validate_record(
        {"modality": "alien_rf", "command": "rm -rf /"})
    assert ok is False
    assert any("executable" in w or "command" in w for w in why)
