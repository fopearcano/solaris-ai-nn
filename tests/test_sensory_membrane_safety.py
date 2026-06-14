"""Sensory membrane safety: write/network/command/unbounded-scan blocked."""

from __future__ import annotations

from solaris_ai_nn.sensory_membrane import SensoryMembraneSafetyValidator


def test_invariants_false():
    sv = SensoryMembraneSafetyValidator()
    assert sv.can_write_sources() is False
    assert sv.can_execute() is False
    assert sv.can_network() is False
    assert sv.can_capture_devices() is False


def test_write_blocked():
    sv = SensoryMembraneSafetyValidator()
    assert not sv.validate_operation("write to source").safe
    assert not sv.validate_operation("delete file").safe
    assert sv.validate_operation("read line").safe


def test_network_blocked():
    sv = SensoryMembraneSafetyValidator()
    assert not sv.validate_operation("open http socket").safe


def test_command_payload_blocked():
    sv = SensoryMembraneSafetyValidator()
    assert not sv.validate_operation("exec payload").safe
    assert not sv.validate_operation("treat input as command").safe
    assert not sv.validate_input_is_not_command("operator_command").safe
    assert sv.validate_input_is_not_command("environmental_input").safe


def test_device_capture_blocked():
    sv = SensoryMembraneSafetyValidator()
    assert not sv.validate_operation("camera capture").safe


def test_unbounded_scan_blocked():
    sv = SensoryMembraneSafetyValidator()
    assert not sv.validate_scan(recursive=False, recursion_allowed=False,
                                max_file_count=0).safe
    assert not sv.validate_scan(recursive=True, recursion_allowed=False,
                                max_file_count=10).safe
    assert sv.validate_scan(recursive=True, recursion_allowed=True,
                            max_file_count=10).safe


def test_path_outside_root_blocked():
    sv = SensoryMembraneSafetyValidator()
    assert not sv.validate_path("/etc/passwd", ["/tmp/allowed"]).safe
