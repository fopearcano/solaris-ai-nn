"""Sensory <-> Conscience: spine phase, bounded profile, bus receives events."""

from __future__ import annotations

import json

from solaris_ai_nn.conscience import (
    ConscienceOrchestrator,
    RunContext,
    RunMode,
    ScenarioProfileRegistry,
)
from solaris_ai_nn.conscience.spine import SpinePhase


def test_read_only_sensory_poll_phase_exists():
    assert SpinePhase.READ_ONLY_SENSORY_POLL == "read_only_sensory_poll"
    order = SpinePhase.ORDER
    assert order.index(SpinePhase.HEARTBEAT) \
        < order.index(SpinePhase.READ_ONLY_SENSORY_POLL) \
        < order.index(SpinePhase.STIMULUS_INGESTION)


def _ctx(tmp_path):
    inroot = tmp_path / "inputs"
    inroot.mkdir()
    path = inroot / "e.jsonl"
    path.write_text("".join(json.dumps({"i": i}) + "\n" for i in range(6)))
    return RunContext(
        mode=RunMode.SHORT_DEMO, state_dir=str(tmp_path / "state"),
        max_steps=8,
        enabled_modules=["bridge", "ecology", "governance", "ops",
                         "sensory_membrane"],
        metadata={"sensory_allowed_roots": [str(inroot)],
                  "sensory_real_sources": True,
                  "sensory_simulated_only": False,
                  "sensory_sources": [{"source_id": "j1",
                                       "source_type": "jsonl_file",
                                       "path": str(path), "enabled": True}]})


def test_membrane_profile_runs_bounded(tmp_path):
    orch = ConscienceOrchestrator()
    orch.configure(_ctx(tmp_path))
    orch.initialize()
    orch.run()
    assert orch.step_count == 8
    assert orch.counts.get("sensory_poll", 0) > 0
    assert "sensory_membrane" not in orch.summary()["degraded_modules"]


def test_bus_receives_sensory_event(tmp_path):
    orch = ConscienceOrchestrator()
    orch.configure(_ctx(tmp_path))
    orch.initialize()
    received = []
    orch.bus.subscribe("stimulus",
                       lambda m: received.append(m) if m.source_module
                       == "sensory_membrane" else None, "t")
    orch.run()
    assert received  # the membrane published environmental stimuli to the bus
    assert received[0].payload.get("origin") == "read_only_environmental_input"


def test_membrane_profiles_exist():
    ids = set(ScenarioProfileRegistry().ids())
    assert {"sensory_membrane_dry_run", "sensory_membrane_short",
            "pilot2_plan_only", "pilot2_read_only_short"} <= ids
