"""LiveFieldComparison: live vs fixture; inconclusive; negative preserved."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.live_field import (
    LiveFeederDescriptor,
    LiveFeederMode,
    LiveFeederRegistry,
    LiveFieldComparison,
    LiveFieldRuntime,
)


def _runtime(tmp_path, modalities=(("rf", "alien_rf"), ("vib",
                                                        "alien_vibration"))):
    base = str(tmp_path / "live")
    os.makedirs(base, exist_ok=True)
    reg = LiveFeederRegistry(live_root=base)
    for mod, hint in modalities:
        path = os.path.join(base, f"{mod}.jsonl")
        with open(path, "w") as fh:
            for i in range(8):
                fh.write(json.dumps({"modality": hint, "v": 0.6,
                                     "ts": float(i)}) + "\n")
        reg.register(LiveFeederDescriptor(
            feeder_id=f"{mod}_feed", source_id=mod, modality=hint,
            mode=LiveFeederMode.LOCAL_FILE, output_path=path))
    rt = LiveFieldRuntime(state_dir=base, live_root=base, registry=reg,
                          max_ticks=30)
    rt.run(live=False)
    return rt


def test_live_vs_fixture_comparison(tmp_path):
    rt = _runtime(tmp_path)
    result = LiveFieldComparison(state_dir=str(tmp_path / "cmp")).run(rt)
    assert "live" in result.arms
    assert "fixture" in result.arms
    assert "passive_parser" in result.arms


def test_missing_modality_inconclusive(tmp_path):
    # An empty live runtime (no feeders) yields an inconclusive comparison.
    base = str(tmp_path / "empty")
    os.makedirs(base, exist_ok=True)
    rt = LiveFieldRuntime(state_dir=base, live_root=base,
                          registry=LiveFeederRegistry(live_root=base))
    rt.run(live=False)
    result = LiveFieldComparison(state_dir=str(tmp_path / "cmp")).run(rt)
    assert result.inconclusive is True


def test_negative_result_preserved(tmp_path):
    rt = _runtime(tmp_path)
    result = LiveFieldComparison(state_dir=str(tmp_path / "cmp")).run(rt)
    # The negative flag is explicit and consistent with the passive comparison.
    assert result.negative_result == (not result.summary["live_beats_passive"])


def test_no_consciousness_claim(tmp_path):
    rt = _runtime(tmp_path)
    result = LiveFieldComparison(state_dir=str(tmp_path / "cmp")).run(rt)
    assert "no claim of consciousness" in result.to_dict()["disclaimer"].lower()
