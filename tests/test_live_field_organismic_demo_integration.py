"""Live field <-> organismic demo: fixture comparison; live registry gated."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.live_field import (
    LiveFeederDescriptor,
    LiveFeederMode,
    LiveFeederRegistry,
    LiveFieldRuntime,
)
from solaris_ai_nn.organismic_demo import (
    MinimalFieldOrganismRunner,
    OrganismicDemoConfig,
)
from solaris_ai_nn.organismic_demo.comparison import live_field_reference_comparison


def _live_runtime(tmp_path):
    base = str(tmp_path / "live")
    os.makedirs(base, exist_ok=True)
    reg = LiveFeederRegistry(live_root=base)
    rf = os.path.join(base, "rf.jsonl")
    with open(rf, "w") as fh:
        for i in range(8):
            fh.write(json.dumps({"modality": "alien_rf", "power": 0.6,
                                 "ts": float(i)}) + "\n")
    reg.register(LiveFeederDescriptor(
        feeder_id="rf_feed", source_id="rf", modality="alien_rf",
        mode=LiveFeederMode.LOCAL_FILE, output_path=rf))
    rt = LiveFieldRuntime(state_dir=base, live_root=base, registry=reg,
                          max_ticks=30)
    rt.run(live=False)
    return rt


def test_fixture_comparison_consumes_live_style_result(tmp_path):
    rt = _live_runtime(tmp_path)
    ref = live_field_reference_comparison(
        rt.live_field_status(), state_dir=str(tmp_path / "ref"), ticks=30)
    assert "fixture" in ref and "live" in ref
    assert "changed_perception_score" in ref["live"]


def test_live_registry_option_blocks_without_governance(tmp_path):
    runner = MinimalFieldOrganismRunner(
        state_dir=str(tmp_path / "demo"),
        config=OrganismicDemoConfig(ticks=20, seed=7),
        use_live_registry=True, governance=None)
    ok = runner.prepare()
    assert ok is False
    assert any("governance" in r for r in runner.refusal_reasons)


def test_demo_runs_normally_without_live_registry(tmp_path):
    runner = MinimalFieldOrganismRunner(
        state_dir=str(tmp_path / "demo2"),
        config=OrganismicDemoConfig(ticks=20, seed=7))
    result = runner.run()
    assert result["refused"] is False
