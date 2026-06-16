"""Roadmap reset: items generated, priorities, no task execution."""

from __future__ import annotations

from solaris_ai_nn.research_baseline import (
    NextCycleRoadmapReset,
    RoadmapItemType,
    RoadmapPriority,
    build_roadmap_reset,
)


def test_roadmap_items_generated_for_validated():
    rm = build_roadmap_reset(
        validated=True, blocked=False, limitations={"limitations": []},
        validation={"validation_missing_count": 0}).to_dict()
    types = {i["item_type"] for i in rm["items"]}
    assert RoadmapItemType.RUN_MINI_SOAK in types
    assert RoadmapItemType.RUN_REPLICATION in types
    assert RoadmapItemType.RUN_ARCHITECTURE_EVOLUTION in types


def test_priorities_required_recommended_optional_blocked():
    rm = build_roadmap_reset(
        validated=False, blocked=True, limitations={"limitations": []},
        validation={"validation_missing_count": 1}).to_dict()
    assert rm["required_count"] >= 1
    assert rm["blocked_count"] >= 1  # soak/replication blocked while blocked
    # Blocked baseline does not recommend a soak as available.
    soak = [i for i in rm["items"]
            if i["item_type"] == RoadmapItemType.RUN_MINI_SOAK]
    assert soak and soak[0]["priority"] == RoadmapPriority.BLOCKED


def test_no_task_execution():
    rm = build_roadmap_reset(
        validated=True, blocked=False, limitations={"limitations": []},
        validation={}).to_dict()
    assert rm["executes_tasks"] is False
    assert rm["creates_branches"] is False
    assert rm["calls_external_tools"] is False
    assert all(i["executed"] is False for i in rm["items"])


def test_limitation_driven_items():
    rm = build_roadmap_reset(
        validated=True, blocked=False,
        limitations={"limitations": [{"category": "fixture_overfit_risk"},
                                     {"category":
                                      "human_label_contamination_risk"}]},
        validation={}).to_dict()
    types = {i["item_type"] for i in rm["items"]}
    assert RoadmapItemType.IMPROVE_FIXTURE_CONTROLS in types
    assert RoadmapItemType.REDUCE_HUMAN_LABEL_CONTAMINATION in types


def test_unknown_item_ignored():
    rm = NextCycleRoadmapReset()
    rm.add("not_a_real_item")
    assert rm.to_dict()["roadmap_item_count"] == 0
