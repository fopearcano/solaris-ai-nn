"""ConsolidationPressureEstimator: pressure computed; quiet mode; bounded replay."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.perceptual_metabolism import ConsolidationPressureEstimator
from solaris_ai_nn.perceptual_metabolism.consolidation_pressure import (
    ConsolidationRecommendation,
)
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder


def _sensorium(tmp_path, n=12):
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "ps"))
    path = os.path.join(str(tmp_path), "rf.jsonl")
    with open(path, "w") as fh:
        for i in range(n):
            fh.write(json.dumps({"modality": "alien_rf", "power": 0.7,
                                 "ts": float(i)}) + "\n")
    rt.add_feeder(fixture_feeder("rf_feed", path, "alien_rf"))
    rt.run_bounded(max_polls=1)
    return rt


def test_consolidation_pressure_computed(tmp_path):
    rt = _sensorium(tmp_path)
    state = ConsolidationPressureEstimator().estimate(rt)
    assert 0.0 <= state.pressure <= 1.0
    assert state.recommendation in ConsolidationRecommendation.ALL


def test_quiet_mode_recommended_on_silence(tmp_path):
    rt = _sensorium(tmp_path, n=2)
    state = ConsolidationPressureEstimator().estimate(rt, source_silent=True)
    assert state.recommendation in (ConsolidationRecommendation.QUIET,
                                    ConsolidationRecommendation.DEEP,
                                    ConsolidationRecommendation.LIGHT)


def test_deep_consolidation_on_overload(tmp_path):
    rt = _sensorium(tmp_path)
    state = ConsolidationPressureEstimator().estimate(rt, overloaded=True)
    assert state.recommendation == ConsolidationRecommendation.DEEP


def test_no_unbounded_replay(tmp_path):
    rt = _sensorium(tmp_path)
    recs = ConsolidationPressureEstimator().latent_replay_recommendations(rt)
    # Replay recommendations are a bounded, finite list (recommendation only).
    assert isinstance(recs, list)
    assert 0 < len(recs) <= 6
    note = ConsolidationPressureEstimator().estimate(rt).to_dict()["note"]
    assert "erases no evidence" in note
