"""Research baseline: validated -> soak/replication; blocked -> rollback/revision."""

from __future__ import annotations

from solaris_ai_nn.research_baseline import ResearchBaselineRuntime
from solaris_ai_nn.research_baseline import RoadmapItemType


def _runtime(tmp_path, blocked=False):
    if blocked:
        pm = {"candidate_baseline_status": "blocked_by_safety",
              "critical_regression_count": 2,
              "rollback_recommendation_status": "rollback_recommended",
              "unresolved_blockers": ["critical_safety_regression"]}
        validation = {"unit_tests": {"passed": True},
                      "safety_tests": {"failed": True}}
        safety = False
    else:
        pm = {"candidate_baseline_status": "validated",
              "critical_regression_count": 0,
              "rollback_recommendation_status": "no_rollback_needed",
              "unresolved_blockers": []}
        validation = {"unit_tests": {"passed": True},
                      "safety_tests": {"passed": True},
                      "claimguard": {"safe": True},
                      "safety_invariants": {"passed": True},
                      "mini_soak": {"passed": True}}
        safety = True
    rt = ResearchBaselineRuntime(state_dir=str(tmp_path), baseline_id="rb_v1")
    rt.load_bundle({
        "post_merge": pm,
        "implementation_intake": {"critical_safety_regression_count":
                                  2 if blocked else 0},
        "validation_results": validation, "safety_artifacts": {"passed": safety},
        "snapshot_artifacts": {"replication_report": {"payload": {"r": 1}},
                               "falsification_report": {"payload": {"f": 1}},
                               "soak_dossier": {"payload": {"s": 1}},
                               "evaluation_report": {"payload": {"e": 1}}}})
    rt.run()
    return rt


def test_validated_baseline_recommends_soak_and_replication(tmp_path):
    rt = _runtime(tmp_path)
    assert rt.version.validated
    types = {i["item_type"] for i in rt.roadmap["items"]}
    assert RoadmapItemType.RUN_MINI_SOAK in types
    assert RoadmapItemType.RUN_REPLICATION in types
    assert RoadmapItemType.RUN_FALSIFICATION in types


def test_blocked_baseline_recommends_rollback_revision(tmp_path):
    rt = _runtime(tmp_path, blocked=True)
    assert rt.version.blocked
    types = {i["item_type"] for i in rt.roadmap["items"]}
    assert RoadmapItemType.COLLECT_MISSING_EVIDENCE in types
    assert RoadmapItemType.IMPROVE_SAFETY_EVIDENCE in types
    # Soak is blocked while the baseline is blocked.
    soak = next(i for i in rt.roadmap["items"]
                if i["item_type"] == RoadmapItemType.RUN_MINI_SOAK)
    assert soak["priority"] == "blocked"
