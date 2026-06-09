"""Tests for persistence: checkpoints, manifest, and state round-trip."""

from __future__ import annotations

from solaris_ai_nn.bridges.neural_bridge import SolarisNeuralBridge
from solaris_ai_nn.runtime.persistence import PersistenceManager, StateCheckpoint
from solaris_ai_nn.signals import canonical as C


def _bridge(seed: int = 1) -> SolarisNeuralBridge:
    return SolarisNeuralBridge(action_labels=["a", "b", "c"], seed=seed)


def test_checkpoint_saves_files(tmp_path):
    pm = PersistenceManager(tmp_path / "state")
    bridge = _bridge()
    bridge.process(C.Stimulus(payload="x", intensity=0.5))
    cp = StateCheckpoint.capture(
        bridge, run_id="r1", session_id="s1", session_step=1,
        lifetime_step=1, last_heartbeat_ts=123.0,
    )
    pm.save_checkpoint(cp)
    assert pm.checkpoint_path.exists()
    assert pm.telemetry_path.exists()


def test_checkpoint_loads_files(tmp_path):
    pm = PersistenceManager(tmp_path / "state")
    bridge = _bridge()
    bridge.process(C.Stimulus(payload="x", intensity=0.5))
    pm.save_checkpoint(
        StateCheckpoint.capture(
            bridge, run_id="r1", session_id="s1", session_step=3,
            lifetime_step=9, last_heartbeat_ts=1.0,
        )
    )
    loaded = pm.load_checkpoint()
    assert loaded is not None
    assert loaded.run_id == "r1"
    assert loaded.lifetime_step == 9
    assert len(loaded.reservoir_state) == bridge.esn.n_reservoir


def test_reservoir_and_readout_survive_reload(tmp_path):
    pm = PersistenceManager(tmp_path / "state")
    src = _bridge(seed=5)
    # Drive + learn so state and weights are non-trivial.
    for p in ("light", "noise", "food", "light"):
        src.process(C.Stimulus(payload=p, intensity=0.6))
        src.react(C.Reaction(valence=1.0))
    pm.save_checkpoint(
        StateCheckpoint.capture(
            src, run_id="r", session_id="s", session_step=4,
            lifetime_step=4, last_heartbeat_ts=1.0,
        )
    )

    # Fresh bridge with the SAME seed (so reservoir matrices match), then restore.
    dst = _bridge(seed=5)
    assert dst.esn.state != src.esn.state  # different before restore
    pm.load_checkpoint().restore_into(dst)
    assert dst.esn.state == src.esn.state
    assert dst.readout.weights == src.readout.weights
    assert dst.habit.weights == src.habit.weights


def test_manifest_tracks_graceful_shutdown(tmp_path):
    pm = PersistenceManager(tmp_path / "state")
    assert pm.load_manifest() is None
    pm.save_manifest({"run_id": "r", "last_graceful_shutdown": False, "lifetime_steps": 10})
    assert pm.has_previous_state()
    m = pm.load_manifest()
    assert m["last_graceful_shutdown"] is False
    pm.save_manifest({"run_id": "r", "last_graceful_shutdown": True, "lifetime_steps": 20})
    assert pm.load_manifest()["last_graceful_shutdown"] is True


def test_checkpoint_to_dict_roundtrip(tmp_path):
    bridge = _bridge()
    bridge.process(C.Stimulus(payload="x"))
    cp = StateCheckpoint.capture(
        bridge, run_id="r", session_id="s", session_step=1,
        lifetime_step=1, last_heartbeat_ts=1.0,
    )
    rebuilt = StateCheckpoint.from_dict(cp.to_dict())
    assert rebuilt.reservoir_state == cp.reservoir_state
    assert rebuilt.readout_labels == cp.readout_labels
