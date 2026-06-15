"""ExternalFeederDescriptor: serialises; no control granted; real/fixture/manual."""

from __future__ import annotations

from solaris_ai_nn.plural_sensorium import (
    ExternalFeederDescriptor,
    FeederSourceType,
    FeederTrustLevel,
    fixture_feeder,
)


def test_feeder_descriptor_serializes():
    f = ExternalFeederDescriptor(
        feeder_id="rf", source_type=FeederSourceType.SDR_FEATURE_EXPORTER,
        path="/x/rf.jsonl", modality_hint="alien_rf")
    data = f.to_dict()
    assert data["feeder_id"] == "rf"
    assert data["source_type"] == "sdr_feature_exporter"


def test_feeder_does_not_grant_control():
    f = fixture_feeder("rf", "/x/rf.jsonl", "alien_rf")
    assert f.read_only is True
    assert f.controllable_by_solaris is False
    assert f.to_dict()["controllable_by_solaris"] is False


def test_real_fixture_manual_supported():
    real = ExternalFeederDescriptor(
        feeder_id="r", source_type=FeederSourceType.SENSOR_LOGGER, path="/x")
    fixture = fixture_feeder("f", "/x")
    manual = ExternalFeederDescriptor(
        feeder_id="m", source_type=FeederSourceType.MANUAL_LOG, path="/x",
        trust_level=FeederTrustLevel.MANUAL)
    assert real.is_real_world and real.requires_governance
    assert not fixture.is_real_world and not fixture.requires_governance
    assert manual.source_type == "manual_log"


def test_unknown_source_type_normalized():
    f = ExternalFeederDescriptor(feeder_id="u", source_type="bogus", path="/x")
    assert f.source_type == FeederSourceType.UNKNOWN_EXTERNAL
