"""Self-boundary consumes receptor state and feeder provenance -> attribution."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.self_boundary import SelfBoundaryRuntime


def _sensorium(tmp_path):
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "ps"))
    for mod in ("alien_rf", "alien_vibration"):
        path = os.path.join(str(tmp_path), f"{mod}.jsonl")
        with open(path, "w") as fh:
            for i in range(12):
                fh.write(json.dumps({"modality": mod, "v": 0.6,
                                     "ts": float(i)}) + "\n")
        rt.add_feeder(fixture_feeder(f"{mod}_feed", path, mod))
    rt.run_bounded(max_polls=3)
    return rt


def test_consumes_receptor_state(tmp_path):
    sb = SelfBoundaryRuntime(state_dir=str(tmp_path / "sb"),
                             sensorium=_sensorium(tmp_path), max_ticks=1)
    sb.update(tick=0)
    assert sb.body_schema.part_count > 0
    # Each receptor body part links to its external source.
    assert any(p.source_link for p in sb.body_schema.parts.values())


def test_consumes_feeder_provenance(tmp_path):
    snap = {"feeders": [{"feeder_id": "rf_feed"}, {"feeder_id": "vib_feed"}]}
    sb = SelfBoundaryRuntime(state_dir=str(tmp_path / "sb"),
                             sensorium=_sensorium(tmp_path),
                             feeder_monitor_snapshot=snap, max_ticks=1)
    sb.update(tick=0)
    feeder_atts = [a for a in sb.ownership.attributions
                   if a.ownership_type == "external_feeder_artifact"]
    assert len(feeder_atts) >= 2  # feeders attributed as external artifacts


def test_source_attribution_created(tmp_path):
    sb = SelfBoundaryRuntime(state_dir=str(tmp_path / "sb"),
                             sensorium=_sensorium(tmp_path), max_ticks=1)
    sb.update(tick=0)
    assert sb.source_attribution.attributions
    # External sources (read by receptors) are attributed.
    targets = {a.target for a in sb.source_attribution.attributions}
    assert "external_source" in targets
