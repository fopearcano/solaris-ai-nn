"""Research baseline: research protocols exist; operator exposes baseline state."""

from __future__ import annotations

from solaris_ai_nn.communication.input_classifier import OperatorInputClassifier
from solaris_ai_nn.communication.query_router import QueryRouter
from solaris_ai_nn.evaluation.protocols import PROTOCOLS
from solaris_ai_nn.operator_console.profile_catalog import ProfileCatalog
from solaris_ai_nn.research_baseline import ResearchBaselineRuntime


def _runtime():
    rt = ResearchBaselineRuntime(
        state_dir=".solaris_ai_nn_research_baseline/opx", baseline_id="rb_v1",
        parent_baseline_id="b1")
    rt.load_bundle({
        "post_merge": {"candidate_baseline_status": "validated",
                       "critical_regression_count": 0,
                       "rollback_recommendation_status": "no_rollback_needed",
                       "unresolved_blockers": []},
        "implementation_intake": {"critical_safety_regression_count": 0,
                                  "spec_compliance_status": "satisfied"},
        "validation_results": {"unit_tests": {"passed": True},
                               "safety_tests": {"passed": True},
                               "claimguard": {"safe": True},
                               "safety_invariants": {"passed": True}},
        "safety_artifacts": {"passed": True},
        "snapshot_artifacts": {"evaluation_report": {"payload": {"e": 1}}},
        "available_anchors": {"parent_baseline": "b1"}})
    rt.run()
    return rt


def test_research_protocols_exist():
    for name in ("research_baseline_protocol", "baseline_version_protocol",
                 "snapshot_manifest_protocol", "repro_bundle_protocol",
                 "capability_map_protocol", "limitation_registry_protocol",
                 "safety_boundary_statement_protocol",
                 "validation_summary_protocol", "comparison_anchor_protocol",
                 "roadmap_reset_protocol"):
        assert name in PROTOCOLS


def test_operator_catalog_exposes_research_baseline():
    entries = [e for e in ProfileCatalog()._entries.values()
               if e.source_package == "research_baseline"]
    assert entries


def test_operator_exposes_baseline_capability_roadmap():
    rt = _runtime()
    router = QueryRouter(components={"research_baseline": rt})
    clf = OperatorInputClassifier()
    cur = router.route_query(clf.classify("what is the current research baseline?"))
    assert "baseline" in cur.text.lower()
    lim = router.route_query(clf.classify("what are its limitations?"))
    assert "limitation" in lim.text.lower()
    nxt = router.route_query(clf.classify("what should I run next?"))
    assert "roadmap" in nxt.text.lower()


def test_operator_safe_answers():
    router = QueryRouter(components={})
    clf = OperatorInputClassifier()
    rel = router.route_query(clf.classify("is this a release?"))
    assert "not a product release" in rel.text.lower()
    tag = router.route_query(clf.classify("did Solaris create a Git tag?"))
    assert "did not run git" in tag.text.lower()
    con = router.route_query(clf.classify("does this prove consciousness?"))
    assert "does not prove consciousness" in con.text.lower()
