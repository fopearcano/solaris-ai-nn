"""RoadmapCompiler: roadmap generated; evidence refs; forbidden item rejected."""

from __future__ import annotations

import os

from solaris_ai_nn.architecture_evolution import (
    RoadmapCompiler,
    RoadmapHorizon,
    RoadmapItem,
    RoadmapItemType,
)


def test_roadmap_generated(tmp_path):
    rc = RoadmapCompiler(base_dir=str(tmp_path))
    items = rc.compile(lifecycle_assessments={
        "latent": {"lifecycle_class": "candidate_for_pruning",
                   "evidence_refs": ["r"]}})
    paths = rc.write(items)
    assert items
    assert os.path.exists(paths["markdown"]) and os.path.exists(paths["json"])


def test_evidence_refs_included(tmp_path):
    rc = RoadmapCompiler(base_dir=str(tmp_path))
    items = rc.compile(lifecycle_assessments={
        "world_model": {"lifecycle_class": "promote_to_core",
                        "evidence_refs": ["research:world_model"]}})
    promote = [i for i in items if i.item_type ==
               RoadmapItemType.PROMOTE_MODULE_PLAN]
    assert promote and "research:world_model" in promote[0].evidence_refs


def test_forbidden_actuation_item_rejected(tmp_path):
    rc = RoadmapCompiler(base_dir=str(tmp_path))
    forbidden = RoadmapItem(item_type=RoadmapItemType.RUN_EXPERIMENT,
                            title="connect a robot actuator",
                            rationale="real_world device control")
    items = rc.compile(extra_items=[forbidden])
    item = items[0]
    assert item.horizon == RoadmapHorizon.REJECTED
    assert item.rejected_reason


def test_safety_failing_prioritizes_safety_first(tmp_path):
    rc = RoadmapCompiler(base_dir=str(tmp_path))
    items = rc.compile(safety_critical_failing=True)
    assert items[0].item_type == RoadmapItemType.IMPROVE_SAFETY_INVARIANT
    assert items[0].horizon == RoadmapHorizon.IMMEDIATE


def test_insufficient_evidence_becomes_retest(tmp_path):
    rc = RoadmapCompiler(base_dir=str(tmp_path))
    items = rc.compile(lifecycle_assessments={
        "x": {"lifecycle_class": "insufficient_evidence", "evidence_refs": []}})
    assert any(i.item_type == RoadmapItemType.REPEAT_EXPERIMENT for i in items)
