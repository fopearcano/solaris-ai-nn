"""SensoryEventEnvelope: serialises; provenance required; labels not truth."""

from __future__ import annotations

from solaris_ai_nn.plural_sensorium import AnnotationStatus, SensoryEventEnvelope


def test_envelope_serializes():
    env = SensoryEventEnvelope(
        source_id="rf_feed", source_kind="sdr_feature_exporter",
        modality="radio_frequency", features={"power": 0.6})
    data = env.to_dict()
    assert data["modality"] == "radio_frequency"
    assert data["features"] == {"power": 0.6}
    rebuilt = SensoryEventEnvelope.from_dict(data)
    assert rebuilt.source_id == "rf_feed"


def test_provenance_required():
    env = SensoryEventEnvelope(source_id="rf_feed", source_kind="fixture_replay",
                               modality="radio_frequency", features={"p": 1.0})
    assert env.has_provenance
    assert env.provenance["source_id"] == "rf_feed"


def test_features_primary_annotation_secondary():
    env = SensoryEventEnvelope(
        source_id="t", source_kind="manual_log", modality="human_textual",
        features={"length": 5.0}, annotation="a person walked by",
        annotation_status=AnnotationStatus.HUMAN_LABEL_EXTERNAL)
    # The human label is present but flagged as non-ground-truth contamination.
    assert env.has_human_label
    assert "human_label_present" in env.contamination_flags
    assert env.features  # features remain primary


def test_read_only_and_not_mutable():
    env = SensoryEventEnvelope(source_id="x", source_kind="manual_log",
                               modality="unknown_field", features={},
                               read_only=False, source_mutable_by_solaris=True)
    # These are forced regardless of constructor arguments.
    assert env.read_only is True
    assert env.source_mutable_by_solaris is False


def test_annotation_optional():
    env = SensoryEventEnvelope(source_id="x", source_kind="manual_log",
                               modality="vibration", features={"a": 1.0})
    assert env.annotation is None
    assert env.annotation_status == AnnotationStatus.NONE
    assert not env.has_human_label
