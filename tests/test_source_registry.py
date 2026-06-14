"""Sensory source registry: registration, validation, health logging."""

from __future__ import annotations

import os

from solaris_ai_nn.sensory_membrane import (
    SensorySourceConfig,
    SensorySourceRegistry,
)


def test_source_registered(tmp_path):
    root = tmp_path / "in"
    root.mkdir()
    (root / "e.jsonl").write_text("{}\n")
    reg = SensorySourceRegistry(state_dir=str(tmp_path),
                                allowed_roots=[str(root)])
    src, errs = reg.register(SensorySourceConfig(
        source_id="s1", source_type="jsonl_file",
        path=str(root / "e.jsonl"), enabled=True))
    assert src is not None and not errs
    assert reg.get("s1") is not None


def test_invalid_source_rejected(tmp_path):
    root = tmp_path / "in"
    root.mkdir()
    reg = SensorySourceRegistry(state_dir=str(tmp_path),
                                allowed_roots=[str(root)])
    src, errs = reg.register(SensorySourceConfig(
        source_id="bad", source_type="text_file", path="/etc/passwd",
        enabled=True))
    assert src is None and errs


def test_health_record_written(tmp_path):
    root = tmp_path / "in"
    root.mkdir()
    reg = SensorySourceRegistry(state_dir=str(tmp_path),
                                allowed_roots=[str(root)])
    reg.register(SensorySourceConfig(source_id="s1", source_type="jsonl_file",
                                     path=str(root / "e.jsonl"), enabled=True))
    assert os.path.exists(str(tmp_path / "sensory_source_health.jsonl"))
    assert os.path.exists(str(tmp_path / "sensory_sources.json"))


def test_disable_and_counts(tmp_path):
    root = tmp_path / "in"
    root.mkdir()
    (root / "e.jsonl").write_text("{}\n")
    reg = SensorySourceRegistry(state_dir=str(tmp_path),
                                allowed_roots=[str(root)])
    reg.register(SensorySourceConfig(source_id="s1", source_type="jsonl_file",
                                     path=str(root / "e.jsonl"), enabled=True))
    assert reg.healthy_count() == 1
    reg.disable("s1")
    assert not reg.enabled_sources()


def test_topology(tmp_path):
    reg = SensorySourceRegistry(state_dir=str(tmp_path), allowed_roots=[])
    topo = reg.topology()
    assert "nodes" in topo and "allowed_roots" in topo
