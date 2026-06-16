"""Research baseline reports: all generated, ClaimGuard-scanned, disclaimer."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.research_baseline import ResearchBaselineRuntime


def _runtime(tmp_path):
    rt = ResearchBaselineRuntime(state_dir=str(tmp_path), baseline_id="rb_v1",
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
                               "safety_invariants": {"passed": True},
                               "mini_soak": {"passed": True}},
        "safety_artifacts": {"passed": True},
        "snapshot_artifacts": {"replication_report": {"payload": {"r": 1}},
                               "falsification_report": {"payload": {"f": 1}},
                               "soak_dossier": {"payload": {"s": 1}},
                               "evaluation_report": {"payload": {"e": 1}}},
        "available_anchors": {"parent_baseline": "b1"}})
    rt.run()
    return rt


def test_all_reports_generated(tmp_path):
    out = _runtime(tmp_path).write_artifacts()
    names = {os.path.basename(p) for p in out["documents"]}
    for expected in ("RESEARCH_BASELINE_REPORT.md", "RESEARCH_BASELINE_REPORT.json",
                     "BASELINE_VERSION.md", "SNAPSHOT_MANIFEST.md",
                     "CAPABILITY_MAP.md", "LIMITATION_REGISTRY.md",
                     "SAFETY_BOUNDARY_STATEMENT.md", "VALIDATION_SUMMARY.md",
                     "COMPARISON_ANCHORS.md", "NEXT_CYCLE_ROADMAP.md",
                     "OPERATOR_RUNBOOK.md", "REPRO_BUNDLE_MANIFEST.json",
                     "REPRO_BUNDLE_README.md"):
        assert expected in names


def test_claim_guard_scans_reports(tmp_path):
    report = _runtime(tmp_path).write_artifacts()["report"]
    assert report["claim_guard_safe"] is True


def test_research_baseline_disclaimer_present(tmp_path):
    out = _runtime(tmp_path).write_artifacts()
    with open(out["json"], encoding="utf-8") as fh:
        data = json.load(fh)
    proofs = " ".join(data["sections"]["what_this_does_not_do"]).lower()
    assert "research baseline, not a product release" in proofs
    assert "no git tag was created" in proofs
    assert "no github release was created" in proofs
