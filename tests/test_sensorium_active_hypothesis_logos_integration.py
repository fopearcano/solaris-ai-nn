"""Plural sensorium <-> active perception / hypothesis / LOGOS integration."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.plural_sensorium import (
    PluralSensoriumRuntime,
    Receptor,
    SensoriumAttentionPolicy,
    SensoryField,
    fixture_feeder,
)
from solaris_ai_nn.plural_sensorium.attention import AttentionAction
from solaris_ai_nn.plural_sensorium.event_envelope import SensoryEventEnvelope


def test_active_perception_focus_within_bounds():
    policy = SensoriumAttentionPolicy(max_shifts_per_tick=3)
    r = Receptor(receptor_id="rf", modality="radio_frequency", source_id="rf")
    r.observe(SensoryEventEnvelope(source_id="rf", source_kind="fixture_replay",
                                   modality="radio_frequency",
                                   features={"power": 2.0}))
    state = SensoryField().update([r], novelty=0.9)
    shifts = policy.decide(state, [r])
    assert len(shifts) <= 3
    assert any(s.action == AttentionAction.FOCUS_MODALITY for s in shifts)


def test_hypothesis_source_includes_modality_and_provenance(tmp_path):
    path = os.path.join(tmp_path, "rf.jsonl")
    with open(path, "w") as fh:
        for i in range(8):
            fh.write(json.dumps({"modality": "alien_rf", "v": 0.7,
                                 "ts": float(i)}) + "\n")
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path) + "/s")
    rt.add_feeder(fixture_feeder("rf", path, "alien_rf"))
    rt.run_bounded(max_polls=1)
    assert rt.hypotheses
    hyp = rt.hypotheses[0]
    assert "modality" in hyp["evidence_scope"]
    assert "source_id" in hyp["evidence_scope"]
    assert "provenance" in hyp


def test_logos_tension_expected_signal_vs_absence(tmp_path):
    path = os.path.join(tmp_path, "rf.jsonl")
    with open(path, "w") as fh:
        for i in range(5):
            fh.write(json.dumps({"modality": "alien_rf", "v": 0.5,
                                 "ts": float(i)}) + "\n")
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path) + "/s")
    rt.add_feeder(fixture_feeder("rf", path, "alien_rf"))
    rt.run_bounded(max_polls=1)
    # Register an expectation that will be overdue, then poll again to detect it.
    rt.absence.register_expectation("rf", "radio_frequency",
                                    expected_interval=0.01, last_seen=0.0)
    rt.poll_once()
    assert any(t["tension"] == "expected_signal_vs_absence"
               for t in rt.logos_tensions)
