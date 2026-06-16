"""Research cycle manifest: refs, from_dict round-trip, persistence."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.research_cycle import (
    ResearchCycleManifest,
    ResearchCycleScope,
)


def test_from_dict_round_trip():
    m = ResearchCycleManifest.from_dict({
        "identity": {"cycle_id": "cycle_3", "parent_cycle_id": "cycle_2",
                     "baseline_id": "b2"},
        "roadmap_refs": ["NEXT_CYCLE_ROADMAP.md"],
        "current_cycle_state": "research_baseline_validated"})
    assert m.identity.cycle_id == "cycle_3"
    assert m.identity.parent_cycle_id == "cycle_2"
    assert m.roadmap_refs == ["NEXT_CYCLE_ROADMAP.md"]
    assert m.current_cycle_state == "research_baseline_validated"


def test_to_dict_declares_no_actions():
    d = ResearchCycleManifest().to_dict()
    assert d["creates_branches"] is False
    assert d["runs_experiments"] is False
    assert d["modifies_source"] is False
    assert d["identity"]["biological_lineage"] is False


def test_persist_writes_manifest_and_history(tmp_path):
    m = ResearchCycleManifest.from_dict({"identity": {"cycle_id": "cycle_1"}})
    paths = m.persist(str(tmp_path))
    assert os.path.isfile(paths["manifest"])
    assert os.path.isfile(paths["history"])
    with open(paths["manifest"], encoding="utf-8") as fh:
        data = json.load(fh)
    assert data["identity"]["cycle_id"] == "cycle_1"


def test_scope_default():
    assert ResearchCycleManifest().scope == ResearchCycleScope.SINGLE_CYCLE
