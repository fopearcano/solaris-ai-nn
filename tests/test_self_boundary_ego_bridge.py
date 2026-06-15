"""Self-boundary bridges the older ego module without duplicate conflict."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.self_boundary import SelfBoundaryRuntime


def _runtime(tmp_path):
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "ps"))
    path = os.path.join(str(tmp_path), "rf.jsonl")
    with open(path, "w") as fh:
        for i in range(10):
            fh.write(json.dumps({"modality": "alien_rf", "power": 0.6,
                                 "ts": float(i)}) + "\n")
    rt.add_feeder(fixture_feeder("rf_feed", path, "alien_rf"))
    rt.run_bounded(max_polls=3)
    sb = SelfBoundaryRuntime(state_dir=str(tmp_path / "sb"), sensorium=rt,
                             max_ticks=2)
    sb.run_bounded()
    return sb


def test_older_ego_module_importable():
    # The older ego/ package coexists; self_boundary does not duplicate it.
    from solaris_ai_nn import ego

    assert hasattr(ego, "SelfModel")
    assert hasattr(ego, "OwnershipAttributor")  # ego's own, distinct class


def test_bridge_summary_produced(tmp_path):
    sb = _runtime(tmp_path)
    summary = sb.ego_bridge_summary()
    assert "boundary_confidence" in summary
    assert "receptor_body_part_count" in summary
    assert "operational only" in summary["note"]


def test_bridge_updates_ego_model_without_conflict(tmp_path):
    sb = _runtime(tmp_path)
    from solaris_ai_nn.ego import SelfModel

    model = SelfModel()
    # Bridging offers self-boundary context; it must not raise or clobber ego.
    summary = sb.ego_bridge_summary(ego_model=model)
    assert summary["boundary_confidence"] >= 0.0


def test_self_boundary_ownership_distinct_from_ego():
    from solaris_ai_nn import ego
    from solaris_ai_nn import self_boundary

    # Both define an OwnershipAttributor; they are distinct classes (no clobber).
    assert ego.OwnershipAttributor is not self_boundary.OwnershipAttributor
