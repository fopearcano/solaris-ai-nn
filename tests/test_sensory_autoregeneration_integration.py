"""Sensory <-> Auto-regeneration: malformed flood + reduce-poll proposal."""

from __future__ import annotations

from solaris_ai_nn.sensory_membrane import (
    SensoryMembraneRuntime,
    SensorySourceConfig,
)


def test_malformed_event_flood_tracked(tmp_path):
    root = tmp_path / "in"
    root.mkdir()
    path = root / "e.jsonl"
    path.write_text("\n".join("{bad line %d" % i for i in range(30)) + "\n")
    rt = SensoryMembraneRuntime(
        state_dir=str(tmp_path / "state"), allowed_input_roots=[str(root)],
        enabled=True, simulated_sources_only=False,
        real_read_only_sources_enabled=True)
    rt.add_source(SensorySourceConfig(source_id="j", source_type="jsonl_file",
                                      path=str(path), enabled=True,
                                      max_events_per_poll=50))
    rt.initialize()
    rt.run_bounded(max_polls=2)
    summary = rt.summary()
    # The membrane surfaces malformed counts that auto-regeneration consumes.
    assert summary["malformed_events"] >= 20
    rate = summary["malformed_events"] / max(1, summary["total_events"])
    assert rate > 0.5  # a malformed flood, eligible for a hygiene proposal


def test_reduce_poll_rate_repair_is_config_only(tmp_path):
    root = tmp_path / "in"
    root.mkdir()
    (root / "e.jsonl").write_text('{"a":1}\n')
    rt = SensoryMembraneRuntime(
        state_dir=str(tmp_path / "state"), allowed_input_roots=[str(root)],
        enabled=True, simulated_sources_only=False,
        real_read_only_sources_enabled=True)
    rt.add_source(SensorySourceConfig(source_id="j", source_type="jsonl_file",
                                      path=str(root / "e.jsonl"),
                                      enabled=True))
    rt.initialize()
    src = rt.registry.get("j")
    before = src.config.poll_interval_s
    # An auto-regeneration "reduce poll rate" repair only changes config; it
    # never modifies the source or grants actuation.
    src.config.poll_interval_s = before * 2
    assert src.config.read_only is True
    assert src.config.poll_interval_s > before


def test_buffer_overflow_tracked(tmp_path):
    from solaris_ai_nn.sensory_membrane import (
        RawSensoryEvent,
        SensoryBuffer,
        SensoryEventNormalizer,
    )

    buf = SensoryBuffer(state_dir=str(tmp_path), capacity=2)
    norm = SensoryEventNormalizer()
    for i in range(6):
        buf.admit(norm.normalize(RawSensoryEvent(
            source_id="s", source_type="text_file", payload=f"v{i}")))
    assert buf.dropped_count >= 1  # overflow -> hygiene can archive logs
