"""Self-boundary: LOGOS tensions emitted; memory events; latent markers kept."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.self_boundary import BoundaryMarker, SelfBoundaryRuntime


def _runtime(tmp_path):
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "ps"))
    for mod in ("alien_rf", "alien_vibration"):
        path = os.path.join(str(tmp_path), f"{mod}.jsonl")
        with open(path, "w") as fh:
            for i in range(12):
                fh.write(json.dumps({"modality": mod, "v": 0.6,
                                     "ts": float(i)}) + "\n")
        rt.add_feeder(fixture_feeder(f"{mod}_feed", path, mod))
    rt.run_bounded(max_polls=3)
    sb = SelfBoundaryRuntime(state_dir=str(tmp_path / "sb"), sensorium=rt,
                             feeder_monitor_snapshot={"feeders": [
                                 {"feeder_id": "rf_feed"}]}, max_ticks=2)
    sb.run_bounded()
    return sb


def test_logos_tensions_emitted(tmp_path):
    sb = _runtime(tmp_path)
    tensions = sb.logos_tensions()
    assert tensions
    from solaris_ai_nn.logos_complexity.tension import TensionType
    assert all(t.tension_type in TensionType.ALL for t in tensions)
    assert any("self_boundary_tension" in t.metadata for t in tensions)


def test_memory_stores_boundary_events(tmp_path):
    sb = _runtime(tmp_path)
    events = sb.memory_events()
    assert events
    # Boundary events and identity events are available for memory storage.
    assert os.path.isfile(tmp_path / "sb" / "boundary_events.jsonl")
    assert os.path.isfile(tmp_path / "sb" / "identity_trace.jsonl")


def test_latent_replay_preserves_markers(tmp_path):
    sb = _runtime(tmp_path)
    # A replayed record keeps its marker; a replay marker is not observation.
    m = sb.sim_boundary.mark("replay_1", BoundaryMarker.REPLAY)
    assert m.marker == BoundaryMarker.REPLAY
    assert m.is_observation is False
    # A replay must never be promotable to observation evidence implicitly:
    # observation markers and replay markers stay distinct.
    obs = sb.sim_boundary.mark("obs_1", BoundaryMarker.OBSERVATION)
    assert obs.marker != m.marker
