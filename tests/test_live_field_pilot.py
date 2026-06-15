"""LiveFieldPilot: preflight runs; live needs governance; bounded; fallback."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.live_field import (
    LiveFeederDescriptor,
    LiveFeederMode,
    LiveFeederRegistry,
    LiveFieldPilot,
    LiveFieldPilotConfig,
    LiveFieldRuntime,
)


def _runtime(tmp_path):
    base = str(tmp_path / "live")
    os.makedirs(base, exist_ok=True)
    reg = LiveFeederRegistry(live_root=base)
    rf = os.path.join(base, "rf.jsonl")
    with open(rf, "w") as fh:
        for i in range(6):
            fh.write(json.dumps({"modality": "alien_rf", "power": 0.6,
                                 "ts": float(i)}) + "\n")
    reg.register(LiveFeederDescriptor(
        feeder_id="rf_feed", source_id="rf", modality="alien_rf",
        mode=LiveFeederMode.LOCAL_FILE, output_path=rf))
    return base, LiveFieldRuntime(state_dir=base, live_root=base, registry=reg,
                                  max_ticks=30)


def test_preflight_and_phases_run(tmp_path):
    base, rt = _runtime(tmp_path)
    pilot = LiveFieldPilot(state_dir=base, runtime=rt,
                           config=LiveFieldPilotConfig(max_ticks=30, live=False))
    result = pilot.run()
    assert result.refused is False
    assert "preflight" in result.phases_run
    assert "report" in result.phases_run


def test_live_mode_requires_governance(tmp_path):
    base, rt = _runtime(tmp_path)
    pilot = LiveFieldPilot(state_dir=base, runtime=rt,
                           config=LiveFieldPilotConfig(live=True, max_ticks=20))
    result = pilot.run(governance_approved=False)
    assert result.refused is True
    assert any("governance" in r for r in result.refusal_reasons)


def test_fixture_fallback_allowed(tmp_path):
    base, rt = _runtime(tmp_path)
    pilot = LiveFieldPilot(state_dir=base, runtime=rt,
                           config=LiveFieldPilotConfig(live=False,
                                                       fixture_fallback=True,
                                                       max_ticks=20))
    result = pilot.run()
    assert result.refused is False


def test_no_unbounded_pilot():
    cfg = LiveFieldPilotConfig()
    # The pilot is always bounded by a hard cap and a tick limit.
    assert cfg.hard_cap_s > 0
    assert cfg.max_ticks > 0
    assert cfg.duration_s <= cfg.hard_cap_s
