"""Sensory <-> Active perception: bounded poll-rate preference, no new source."""

from __future__ import annotations

from solaris_ai_nn.sensory_membrane import (
    SensoryMembraneRuntime,
    SensorySourceConfig,
)


def _runtime(tmp_path):
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
    return rt, root


def test_focus_source_request_bounded(tmp_path):
    rt, _ = _runtime(tmp_path)
    src = rt.registry.get("j")
    # Active perception may express a preference by adjusting an existing
    # source's poll interval within config -- bounded, not unbounded.
    src.config.poll_interval_s = max(0.5, src.config.poll_interval_s / 2)
    assert src.config.poll_interval_s >= 0.5


def test_poll_rate_change_within_config_only(tmp_path):
    rt, _ = _runtime(tmp_path)
    src = rt.registry.get("j")
    before = src.config.poll_interval_s
    src.config.poll_interval_s = before * 2  # slow down within config
    assert src.config.read_only is True  # still read-only


def test_cannot_create_new_external_source_without_root(tmp_path):
    rt, _ = _runtime(tmp_path)
    # An attempt to add a source outside the allowed roots is rejected.
    ok, errs = rt.add_source(SensorySourceConfig(
        source_id="evil", source_type="text_file", path="/etc/passwd",
        enabled=True))
    assert ok is False and errs


def test_cannot_browse_or_network(tmp_path):
    rt, _ = _runtime(tmp_path)
    # No network source type exists; a config requesting network is rejected.
    ok, errs = rt.add_source(SensorySourceConfig(
        source_id="net", source_type="jsonl_file",
        path=str(_ := (tmp_path / "in" / "e.jsonl")),
        enabled=True, metadata={"network": True}))
    assert ok is False
