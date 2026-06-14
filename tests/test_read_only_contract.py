"""Read-only contract: blocks outside-root, writes, commands, input-as-command."""

from __future__ import annotations

from solaris_ai_nn.sensory_membrane import (
    ReadOnlyContractValidator,
    SensorySourceConfig,
)


def test_source_outside_root_blocked():
    v = ReadOnlyContractValidator()
    violations = v.validate_path("/etc/passwd", ["/tmp/allowed"])
    assert violations
    assert v.validate_path("/tmp/allowed/x.jsonl", ["/tmp/allowed"]) == []


def test_write_operation_blocked():
    v = ReadOnlyContractValidator()
    assert v.validate_runtime_access("write to source")
    assert v.validate_runtime_access("delete file")
    assert v.validate_runtime_access("rename source")
    assert v.is_read_only_operation("read line") is True


def test_command_execution_blocked():
    v = ReadOnlyContractValidator()
    assert v.validate_runtime_access("exec payload")
    assert v.validate_runtime_access("shell call")
    assert v.validate_runtime_access("subprocess popen")
    assert v.validate_runtime_access("http network call")


def test_input_text_as_command_blocked():
    v = ReadOnlyContractValidator()
    # "command" is a forbidden runtime operation keyword.
    assert v.validate_runtime_access("treat input as command")


def test_config_requesting_write_rejected():
    v = ReadOnlyContractValidator()
    cfg = SensorySourceConfig(source_id="s", source_type="jsonl_file",
                              metadata={"allow_write": True})
    assert v.validate_source_config(cfg)


def test_config_requesting_network_or_device_rejected():
    v = ReadOnlyContractValidator()
    net = SensorySourceConfig(source_id="n", source_type="jsonl_file",
                              metadata={"network": True})
    dev = SensorySourceConfig(source_id="d", source_type="jsonl_file",
                              metadata={"device_capture": True})
    assert v.validate_source_config(net)
    assert v.validate_source_config(dev)


def test_snapshot_lists_hard_rules():
    v = ReadOnlyContractValidator()
    snap = v.snapshot()
    assert "no writes to input source" in snap["hard_rules"]
