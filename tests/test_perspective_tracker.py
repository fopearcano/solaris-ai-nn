"""Tests for the perspective tracker."""

from __future__ import annotations

import pytest

from solaris_ai_nn.ego.perspective import (
    MODE_PROPERTIES,
    PerspectiveMode,
    PerspectiveTracker,
)


def test_perspective_shifts_recorded():
    tracker = PerspectiveTracker()
    assert tracker.state.mode == PerspectiveMode.INTERNAL_RUNTIME
    tracker.set_perspective(PerspectiveMode.EMBODIED_SIMULATION,
                            "GridWorld run started")
    assert tracker.state.mode == PerspectiveMode.EMBODIED_SIMULATION
    assert tracker.state.previous_mode == PerspectiveMode.INTERNAL_RUNTIME
    assert tracker.shift_count == 1
    assert tracker.shifts[-1]["reason"] == "GridWorld run started"
    # Setting the same mode again is not a shift.
    tracker.set_perspective(PerspectiveMode.EMBODIED_SIMULATION, "again")
    assert tracker.shift_count == 1
    with pytest.raises(ValueError):
        tracker.set_perspective("astral_projection")


def test_latent_perspective_marks_offline_evidence():
    tracker = PerspectiveTracker()
    state = tracker.infer_from_context({"latent_mode": "replay"})
    assert state.mode == PerspectiveMode.LATENT_OFFLINE_REPLAY
    assert state.evidence_status == "simulated"
    assert state.actions_allowed is False
    dream = tracker.infer_from_context({"latent_mode": "dream"})
    assert dream.mode == PerspectiveMode.COUNTERFACTUAL_SIMULATION
    assert dream.evidence_status == "counterfactual"
    # Waking restores the default.
    awake = tracker.infer_from_context({"latent_mode": "awake"})
    assert awake.mode == PerspectiveMode.INTERNAL_RUNTIME


def test_sidecar_perspective_marks_observe_only():
    tracker = PerspectiveTracker()
    state = tracker.infer_from_context({"sidecar_attached": True})
    assert state.mode == PerspectiveMode.SOLARIS_SIDECAR_OBSERVER
    assert state.actions_allowed is False
    assert state.action_scope == "none"
    assert state.evidence_status == "observed"
    stream = tracker.infer_from_context({"stream_active": True})
    assert stream.mode == PerspectiveMode.READ_ONLY_STREAM_OBSERVER
    assert stream.actions_allowed is False


def test_all_modes_have_properties_and_no_real_world_scope():
    for mode in PerspectiveMode.ALL:
        allowed, scope, evidence = MODE_PROPERTIES[mode]
        assert scope in ("none", "simulation_only",
                         "internal_maintenance")
        assert evidence in ("observed", "simulated", "counterfactual",
                            "inferred", "unknown")
    snapshot = PerspectiveTracker().snapshot()
    assert "not a point of view" in snapshot["note"]
    assert snapshot["stuck_duration_s"] >= 0.0
