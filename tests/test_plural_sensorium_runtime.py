"""PluralSensoriumRuntime: bounded; dry-run doesn't publish; real needs gov."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.plural_sensorium import (
    ExternalFeederDescriptor,
    FeederSourceType,
    PluralSensoriumRuntime,
    fixture_feeder,
)


def _fixture(tmp_path, modality="alien_rf", n=6):
    path = os.path.join(tmp_path, f"{modality}.jsonl")
    with open(path, "w") as fh:
        for i in range(n):
            fh.write(json.dumps({"modality": modality, "v": 0.5,
                                 "ts": float(i)}) + "\n")
    return path


def test_fixture_runtime_bounded(tmp_path):
    path = _fixture(str(tmp_path))
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "s"),
                                max_events_total=10)
    rt.add_feeder(fixture_feeder("rf", path, "alien_rf"))
    rt.run_bounded(max_polls=20)
    # Never exceeds the total-event budget.
    assert rt.events_ingested <= 10


def test_dry_run_does_not_publish(tmp_path):
    path = _fixture(str(tmp_path))
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "s"), dry_run=True)
    rt.add_feeder(fixture_feeder("rf", path, "alien_rf"))
    rt.run_bounded(max_polls=1)
    # Dry-run ingests/observes but publishes no Stimulus objects.
    assert rt.events_ingested > 0
    assert rt.stimuli == []


def test_real_read_only_mode_requires_governance(tmp_path):
    path = _fixture(str(tmp_path))
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "s"),
                                fixture_mode=False, real_read_only_mode=True,
                                governance=None)
    rt.feeders.append(fixture_feeder("rf", path, "alien_rf"))
    out = rt.run_bounded(max_polls=1)
    assert out["refused"] is True
    assert any("governance" in r for r in out["reasons"])


def test_real_world_feeder_refused_without_governance(tmp_path):
    path = _fixture(str(tmp_path))
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "s"))
    real = ExternalFeederDescriptor(
        feeder_id="sdr", source_type=FeederSourceType.SDR_FEATURE_EXPORTER,
        path=path, modality_hint="alien_rf")
    accepted = rt.add_feeder(real)
    assert accepted is False
    assert rt.refusal_reasons


def test_no_source_modification(tmp_path):
    path = _fixture(str(tmp_path))
    before = open(path).read()
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "s"))
    rt.add_feeder(fixture_feeder("rf", path, "alien_rf"))
    rt.run_bounded(max_polls=2)
    assert open(path).read() == before
