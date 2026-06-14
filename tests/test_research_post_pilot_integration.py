"""Research <-> Post-pilot: Pilot artifacts indexed; missing inconclusive."""

from __future__ import annotations

import os

from solaris_ai_nn.research_lab import (
    ComparisonEngine,
    ResearchResultStore,
)


def test_pilot_artifacts_can_be_indexed(tmp_path):
    # A present Pilot artifact is indexed with a checksum.
    pilot_art = os.path.join(str(tmp_path), "PILOT2_REPORT.json")
    with open(pilot_art, "w") as fh:
        fh.write('{"pilot": 2}')
    store = ResearchResultStore(base_dir=str(tmp_path))
    entry = store.index_artifact("RES_pilot2", pilot_art, label="fixture")
    assert entry.exists is True and entry.checksum


def test_missing_pilot_artifacts_inconclusive(tmp_path):
    store = ResearchResultStore(base_dir=str(tmp_path))
    store.index_artifact("RES_pilot1",
                         os.path.join(str(tmp_path), "PILOT1_MISSING.json"))
    assert store.missing_artifacts()
    # A comparison against a missing Pilot baseline is inconclusive.
    cmp = ComparisonEngine().compare("pilot1", None, "pilot2", {"g": {"x": 1}})
    assert cmp.inconclusive is True


def test_pilot_comparison_when_both_present():
    cmp = ComparisonEngine().compare(
        "pilot1", {"g": {"prediction_accuracy": 0.3}},
        "pilot2", {"g": {"prediction_accuracy": 0.5}})
    assert not cmp.inconclusive
