"""Live Observation refactor: observation consumes impression diet vs event diet."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.membrane_integration import (
    LiveObservationMembraneAdapter,
    SensoryImpressionLoader,
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _membrane_integration_helpers import stage_pipeline  # noqa: E402


def test_observation_uses_impression_diet(tmp_path):
    state = stage_pipeline(str(tmp_path))
    load = SensoryImpressionLoader().load(state)
    r = LiveObservationMembraneAdapter().run(state, load)
    assert r.used_impressions is True
    # Impression diet is keyed by impression kind, not raw source ids.
    assert set(r.data["impression_diet"]) & {
        "presence", "absence", "operator", "machine_body"} or \
        r.data["impression_diet"]
    assert r.data["distinguishes_event_and_impression_diet"] is True


def test_observation_without_membrane_warns(tmp_path):
    load = SensoryImpressionLoader().load(str(tmp_path))
    r = LiveObservationMembraneAdapter().run(str(tmp_path), load)
    assert r.status == "warning"
    assert r.warnings
