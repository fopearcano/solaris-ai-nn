"""Pilot-2 source preflight: valid fixtures pass; outside/network/device fail."""

from __future__ import annotations

import os

from solaris_ai_nn.pilot2 import SourcePreflightRunner
from solaris_ai_nn.sensory_membrane import SensorySourceConfig


def test_valid_fixture_source_passes(tmp_path):
    root = tmp_path / "in"
    root.mkdir()
    jp = root / "e.jsonl"
    jp.write_text('{"a":1}\n')
    runner = SourcePreflightRunner(allowed_roots=[str(root)])
    result = runner.check_source(SensorySourceConfig(
        source_id="j", source_type="jsonl_file", path=str(jp), enabled=True))
    assert result.passed


def test_source_outside_root_fails(tmp_path):
    root = tmp_path / "in"
    root.mkdir()
    runner = SourcePreflightRunner(allowed_roots=[str(root)])
    result = runner.check_source(SensorySourceConfig(
        source_id="bad", source_type="text_file", path="/etc/passwd",
        enabled=True))
    assert not result.passed
    names = {c.name: c.passed for c in result.checks}
    assert names["path_inside_allowed_root"] is False


def test_network_device_config_fails(tmp_path):
    root = tmp_path / "in"
    root.mkdir()
    jp = root / "e.jsonl"
    jp.write_text("{}\n")
    runner = SourcePreflightRunner(allowed_roots=[str(root)])
    result = runner.check_source(SensorySourceConfig(
        source_id="net", source_type="jsonl_file", path=str(jp),
        enabled=True, metadata={"network": True}))
    names = {c.name: c.passed for c in result.checks}
    assert names["read_only_contract_valid"] is False


def test_run_writes_report(tmp_path):
    root = tmp_path / "in"
    root.mkdir()
    jp = root / "e.jsonl"
    jp.write_text("{}\n")
    runner = SourcePreflightRunner(allowed_roots=[str(root)])
    summary = runner.run([SensorySourceConfig(
        source_id="j", source_type="jsonl_file", path=str(jp), enabled=True)],
        state_dir=str(tmp_path))
    assert os.path.exists(str(tmp_path / "source_preflight.json"))
    assert os.path.exists(str(tmp_path / "source_preflight.md"))
    assert summary["all_passed"]
