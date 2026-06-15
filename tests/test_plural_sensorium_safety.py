"""PluralSensoriumSafetyValidator: hardware/SDR/capture/network/command blocked."""

from __future__ import annotations

from solaris_ai_nn.plural_sensorium import HARD_RULES, PluralSensoriumSafetyValidator


def test_capabilities_all_false():
    v = PluralSensoriumSafetyValidator
    assert v.can_access_hardware() is False
    assert v.can_use_sdr() is False
    assert v.can_capture_media() is False
    assert v.can_access_network() is False
    assert v.can_modify_source() is False


def test_hardware_access_blocked():
    v = PluralSensoriumSafetyValidator()
    assert v.validate_operation("open device driver").safe is False
    assert v.validate_operation("control sensor over i2c").safe is False


def test_sdr_driver_blocked():
    v = PluralSensoriumSafetyValidator()
    assert v.validate_operation("tune sdr frequency with hackrf").safe is False


def test_microphone_camera_capture_blocked():
    v = PluralSensoriumSafetyValidator()
    assert v.validate_operation("capture video from camera").safe is False
    assert v.validate_operation("record audio from microphone").safe is False


def test_network_blocked():
    v = PluralSensoriumSafetyValidator()
    assert v.validate_operation("http download a stream").safe is False


def test_sensory_text_command_blocked():
    v = PluralSensoriumSafetyValidator()
    # Sensory text is never an operator command (it is observation only).
    assert v.validate_text_not_command("rm -rf / now").safe is True
    assert v.validate_annotation_not_ground_truth(
        "human_label_external", treated_as_truth=True).safe is False


def test_unbounded_polling_blocked():
    v = PluralSensoriumSafetyValidator()
    assert v.validate_polling_bounded(None, None).safe is False
    assert v.validate_polling_bounded(1000, 30.0).safe is True


def test_hard_rules_present():
    assert "no direct hardware access" in HARD_RULES
    assert "no SDR driver" in HARD_RULES
    assert "no microphone/camera capture" in HARD_RULES
    assert "no human label as ground truth" in HARD_RULES
