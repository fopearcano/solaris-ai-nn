"""Sensory source schema: read-only default, types, serialization."""

from __future__ import annotations

from solaris_ai_nn.sensory_membrane import (
    SensorySource,
    SensorySourceConfig,
    SensorySourceStatus,
    SensorySourceType,
)


def test_read_only_true_by_default():
    cfg = SensorySourceConfig(source_id="s1", source_type="jsonl_file")
    assert cfg.read_only is True
    # read_only is an invariant: even if asked False it stays True.
    cfg2 = SensorySourceConfig(source_id="s2", source_type="text_file",
                               read_only=False)
    assert cfg2.read_only is True


def test_source_types_exist():
    for t in ("jsonl_file", "text_file", "numeric_csv", "folder_snapshot",
              "folder_poll", "event_log", "manual_dump",
              "simulated_camera_metadata", "simulated_audio_metadata",
              "synthetic_sensor", "unknown"):
        assert t in SensorySourceType.ALL


def test_config_serializes_roundtrip():
    cfg = SensorySourceConfig(source_id="s1", source_type="numeric_csv",
                              path="/tmp/x.csv", enabled=True, trust_level="low")
    d = cfg.to_dict()
    assert d["is_simulated"] is False and d["is_real_read_only"] is True
    clone = SensorySourceConfig.from_dict(d)
    assert clone.source_id == "s1" and clone.source_type == "numeric_csv"


def test_simulated_vs_real_classification():
    assert SensorySourceConfig(source_id="c", source_type="simulated_camera_metadata").is_simulated
    assert SensorySourceConfig(source_id="j", source_type="jsonl_file").is_real_read_only


def test_unknown_type_normalized():
    cfg = SensorySourceConfig(source_id="x", source_type="not_a_type")
    assert cfg.source_type == SensorySourceType.UNKNOWN


def test_source_wraps_config_and_health():
    cfg = SensorySourceConfig(source_id="s1", source_type="jsonl_file",
                              enabled=True)
    src = SensorySource(config=cfg, status=SensorySourceStatus.REGISTERED)
    assert src.source_id == "s1" and src.healthy
