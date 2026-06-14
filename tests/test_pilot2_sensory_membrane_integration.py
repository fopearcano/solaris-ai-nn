"""Pilot-2 <-> sensory membrane: preflight hooks, reliability, safe disable."""

from __future__ import annotations

import os

from solaris_ai_nn.pilot2 import SourcePreflightRunner, SourceReliabilityMonitor
from solaris_ai_nn.sensory_membrane import (
    SensoryMembraneRuntime,
    SensorySourceConfig,
)


def _runtime(tmp_path):
    root = tmp_path / "in"
    root.mkdir()
    jp = root / "e.jsonl"
    jp.write_text('{"a":1}\n{"a":2}\n')
    rt = SensoryMembraneRuntime(
        state_dir=str(tmp_path / "state"), allowed_input_roots=[str(root)],
        enabled=True, simulated_sources_only=False,
        real_read_only_sources_enabled=True)
    rt.add_source(SensorySourceConfig(source_id="j", source_type="jsonl_file",
                                      path=str(jp), enabled=True))
    rt.initialize()
    return rt, root, jp


def test_preflight_hooks_work(tmp_path):
    rt, root, jp = _runtime(tmp_path)
    runner = SourcePreflightRunner(allowed_roots=[str(root)])
    configs = [s.config for s in rt.registry.sources.values()]
    summary = runner.run(configs)
    assert summary["all_passed"]


def test_source_reliability_feed_works(tmp_path):
    rt, root, jp = _runtime(tmp_path)
    rt.run_bounded(max_polls=2)
    mon = SourceReliabilityMonitor()
    s = rt.summary()
    mon.observe_poll("j", success=True, events=s["total_events"],
                     provenance=s["total_events"])
    assert "j" in mon.records


def test_source_disable_does_not_delete_source(tmp_path):
    rt, root, jp = _runtime(tmp_path)
    assert os.path.exists(jp)
    out = rt.disable_source("j")
    assert out["disabled"] is True
    assert out["source_deleted"] is False
    # The on-disk source file is untouched.
    assert os.path.exists(jp)
    assert rt.registry.get("j").status == "disabled"
