"""Pilot-2 <-> auto-regeneration: malformed flood + safe source-disable."""

from __future__ import annotations

import os

from solaris_ai_nn.sensory_membrane import (
    SensoryMembraneRuntime,
    SensorySourceConfig,
)


def _runtime(tmp_path, content):
    root = tmp_path / "in"
    root.mkdir()
    jp = root / "e.jsonl"
    jp.write_text(content)
    rt = SensoryMembraneRuntime(
        state_dir=str(tmp_path / "state"), allowed_input_roots=[str(root)],
        enabled=True, simulated_sources_only=False,
        real_read_only_sources_enabled=True)
    rt.add_source(SensorySourceConfig(source_id="j", source_type="jsonl_file",
                                      path=str(jp), enabled=True,
                                      max_events_per_poll=50))
    rt.initialize()
    return rt, jp


def test_malformed_event_flood_signals_source_reduction(tmp_path):
    rt, _ = _runtime(tmp_path, "\n".join("{bad %d" % i for i in range(30))
                     + "\n")
    rt.run_bounded(max_polls=2)
    s = rt.summary()
    rate = s["malformed_events"] / max(1, s["total_events"])
    # A malformed flood (>0.5) is the signal auto-regeneration acts on by
    # proposing a poll-rate reduction / quarantine.
    assert s["malformed_events"] >= 20
    assert rate > 0.5


def test_source_disable_proposal_is_safe(tmp_path):
    rt, jp = _runtime(tmp_path, '{"a":1}\n')
    rt.run_bounded(max_polls=1)
    out = rt.disable_source("j")
    # Disabling is a safe repair: it never deletes or modifies the source.
    assert out["source_deleted"] is False
    assert os.path.exists(jp)
