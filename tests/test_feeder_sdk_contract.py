"""FeederSDKEnvelope: serializes; required fields; human label non-ground-truth."""

from __future__ import annotations

from solaris_ai_nn.feeder_sdk import (
    FeederSDKAnnotationStatus,
    FeederSDKEnvelope,
    FeederSDKTrustLevel,
)


def test_envelope_serializes():
    env = FeederSDKEnvelope(
        feeder_id="rf_feed", source_id="rf",
        source_kind="external_feature_drop", modality="radio_frequency",
        features={"power": 0.7})
    data = env.to_dict()
    assert data["modality"] == "radio_frequency"
    assert data["schema_version"]
    rebuilt = FeederSDKEnvelope.from_dict(data)
    assert rebuilt.feeder_id == "rf_feed"


def test_required_fields_present():
    env = FeederSDKEnvelope(feeder_id="f", source_id="s", source_kind="k",
                            modality="vibration", features={"amplitude": 0.3})
    assert env.has_provenance
    assert env.provenance["source_id"] == "s"
    assert env.provenance["feeder_id"] == "f"


def test_read_only_and_immutable_forced():
    env = FeederSDKEnvelope(feeder_id="f", source_id="s", source_kind="k",
                            modality="magnetic", features={"field": 0.2},
                            read_only=False, source_mutable_by_solaris=True)
    assert env.read_only is True
    assert env.source_mutable_by_solaris is False


def test_human_label_optional_and_non_ground_truth():
    env = FeederSDKEnvelope(
        feeder_id="f", source_id="s", source_kind="manual_log",
        modality="human_textual", features={"length": 5.0},
        annotation="rain started",
        annotation_status=FeederSDKAnnotationStatus.HUMAN_LABEL_EXTERNAL)
    assert env.has_human_label
    assert "human_label_present" in env.contamination_flags
    assert "contains_human_text" in env.privacy_flags
    # The annotation never becomes ground truth.
    assert env.annotation_status == FeederSDKAnnotationStatus.HUMAN_LABEL_EXTERNAL


def test_maps_to_sensory_envelope():
    env = FeederSDKEnvelope(
        feeder_id="rf_feed", source_id="rf",
        source_kind="external_feature_drop", modality="radio_frequency",
        features={"power": 0.7}, trust_level=FeederSDKTrustLevel.FIXTURE
        if hasattr(FeederSDKTrustLevel, "FIXTURE")
        else FeederSDKTrustLevel.SIMULATED_FIXTURE)
    sensory = env.to_sensory_envelope()
    assert sensory.modality == "radio_frequency"
    assert sensory.read_only is True
    assert sensory.source_mutable_by_solaris is False
