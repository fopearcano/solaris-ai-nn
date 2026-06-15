"""Feature schemas: exist; units documented; privacy notes present."""

from __future__ import annotations

from solaris_ai_nn.feeder_sdk import (
    FEATURE_SCHEMAS,
    all_event_types,
    get_schema,
    schema_coverage,
)


def test_schemas_exist():
    for event_type in ("human_textual_event", "rf_feature_event",
                       "echo_reflection_event", "vibration_event",
                       "magnetic_event", "thermal_gradient_event",
                       "machine_rhythm_event", "absence_silence_event",
                       "cross_modal_hint_event"):
        assert event_type in FEATURE_SCHEMAS


def test_units_documented():
    rf = get_schema("rf_feature_event")
    assert rf.units  # at least one unit documented
    echo = get_schema("echo_reflection_event")
    assert "distance_estimate" in echo.units


def test_privacy_notes_present():
    rf = get_schema("rf_feature_event")
    assert rf.privacy_notes
    assert any("decode" in n.lower() for n in rf.privacy_notes)


def test_schema_coverage_high():
    assert schema_coverage() >= 0.8
    assert len(all_event_types()) >= 13


def test_required_features_validated():
    rf = get_schema("rf_feature_event")
    assert rf.validate_features({}) != []  # missing required 'power'
    assert rf.validate_features({"power": 0.5}) == []
