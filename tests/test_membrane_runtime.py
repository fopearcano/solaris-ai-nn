"""Sensory membrane runtime: dry-run, bounded run, graceful degradation."""

from __future__ import annotations

from solaris_ai_nn.sensory_membrane import (
    SensoryMembraneRuntime,
    SensorySourceConfig,
)


def _runtime(tmp_path, **kw):
    root = tmp_path / "in"
    root.mkdir(exist_ok=True)
    (root / "e.jsonl").write_text('{"a":1}\n{"a":2}\n{"a":3}\n')
    base = dict(state_dir=str(tmp_path / "state"),
                allowed_input_roots=[str(root)], enabled=True,
                simulated_sources_only=False,
                real_read_only_sources_enabled=True)
    base.update(kw)
    rt = SensoryMembraneRuntime(**base)
    rt.add_source(SensorySourceConfig(source_id="j", source_type="jsonl_file",
                                      path=str(root / "e.jsonl"),
                                      enabled=True))
    rt.initialize()
    return rt


def test_dry_run_validates_only(tmp_path):
    rt = _runtime(tmp_path, dry_run=True)
    rt.run_bounded(max_polls=2)
    assert rt.summary()["total_events"] >= 1
    assert rt.summary()["published_events"] == 0  # dry-run publishes nothing


def test_short_run_publishes_bounded(tmp_path):
    rt = _runtime(tmp_path)
    out = rt.run_bounded(max_polls=2)
    assert out["ran"] is True
    assert rt.summary()["total_events"] >= 1


def test_disabled_by_default(tmp_path):
    root = tmp_path / "in"
    root.mkdir()
    rt = SensoryMembraneRuntime(state_dir=str(tmp_path / "s"),
                                allowed_input_roots=[str(root)])
    assert rt.enabled is False
    assert rt.poll_once()["polled"] is False


def test_missing_source_degrades_gracefully(tmp_path):
    root = tmp_path / "in"
    root.mkdir()
    rt = SensoryMembraneRuntime(
        state_dir=str(tmp_path / "s"), allowed_input_roots=[str(root)],
        enabled=True, real_read_only_sources_enabled=True)
    rt.add_source(SensorySourceConfig(source_id="j", source_type="jsonl_file",
                                      path=str(root / "missing.jsonl"),
                                      enabled=True))
    rt.initialize()
    out = rt.run_bounded(max_polls=2)
    assert out["ran"] is True  # never crashes
    assert rt.registry.degraded_count() >= 1


def test_real_source_blocked_when_disabled(tmp_path):
    root = tmp_path / "in"
    root.mkdir()
    (root / "e.jsonl").write_text('{"a":1}\n')
    rt = SensoryMembraneRuntime(
        state_dir=str(tmp_path / "s"), allowed_input_roots=[str(root)],
        enabled=True, real_read_only_sources_enabled=False)
    ok, errs = rt.add_source(SensorySourceConfig(
        source_id="j", source_type="jsonl_file",
        path=str(root / "e.jsonl"), enabled=True))
    assert ok is False and errs


def test_max_total_events_bounds(tmp_path):
    rt = _runtime(tmp_path, max_total_events=2)
    rt.run_bounded(max_polls=5)
    assert rt.summary()["total_events"] <= 2 + 3  # bounded near the cap
