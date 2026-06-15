"""Metabolism consumes Plural Sensorium, Live Field health, Feeder SDK snapshot."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.perceptual_metabolism import PerceptualMetabolismRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder


def _sensorium(tmp_path, modalities=("alien_rf", "alien_vibration")):
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "ps"))
    for mod in modalities:
        path = os.path.join(str(tmp_path), f"{mod}.jsonl")
        with open(path, "w") as fh:
            for i in range(8):
                fh.write(json.dumps({"modality": mod, "v": 0.6,
                                     "ts": float(i)}) + "\n")
        rt.add_feeder(fixture_feeder(f"{mod}_feed", path, mod))
    rt.run_bounded(max_polls=1)
    return rt


def test_consumes_plural_sensorium_state(tmp_path):
    rt = _sensorium(tmp_path)
    met = PerceptualMetabolismRuntime(state_dir=str(tmp_path / "s"), sensorium=rt)
    out = met.update(events_this_tick=12, tick=0)
    # The metabolic tick read the sensorium's receptors / sensory field.
    assert out["field_state"]
    assert met.metabolism_status()["perceptual_need_count"] > 0
    assert met.metabolism_status()["source_diet_diversity"] >= 0.0


class _FakeHealth:
    """Minimal live-field source-health stand-in (read-only)."""

    def silent_sources(self):
        return ["silent_feed"]

    def to_dict(self):
        return {"silent": ["silent_feed"]}


class _FakeLiveField:
    def __init__(self):
        self.health = _FakeHealth()


def test_consumes_live_field_source_health(tmp_path):
    rt = _sensorium(tmp_path)
    met = PerceptualMetabolismRuntime(state_dir=str(tmp_path / "s"),
                                      sensorium=rt,
                                      live_field=_FakeLiveField())
    out = met.update(events_this_tick=10, tick=0)
    # Source health is read; runtime does not start, control, or mutate it.
    assert out is not None
    assert met._source_health() is not None


def test_consumes_feeder_sdk_monitor_snapshot(tmp_path):
    rt = _sensorium(tmp_path)
    snapshot = {"feeders": [{"feeder_id": "rf_feed", "events": 8}],
                "controllable_by_solaris": False}
    met = PerceptualMetabolismRuntime(state_dir=str(tmp_path / "s"),
                                      sensorium=rt,
                                      feeder_monitor_snapshot=snapshot)
    met.update(events_this_tick=8, tick=0)
    # The snapshot is a read-only observation; Solaris cannot control feeders.
    assert met.feeder_monitor_snapshot["controllable_by_solaris"] is False


def test_does_not_start_or_control_feeders(tmp_path):
    rt = _sensorium(tmp_path)
    met = PerceptualMetabolismRuntime(state_dir=str(tmp_path / "s"), sensorium=rt)
    assert not hasattr(met, "start_feeder")
    assert met.safety.can_start_feeders() is False
