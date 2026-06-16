"""Post-merge reports: all generated, ClaimGuard-scanned, disclaimer present."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.post_merge_assimilation import PostMergeAssimilationRuntime


def _runtime(tmp_path):
    rt = PostMergeAssimilationRuntime(state_dir=str(tmp_path),
                                      candidate_baseline_id="b1")
    rt.register_parent("b0", metrics={"sensorium_metrics": 0.5})
    rt.load_bundle({
        "merge_manifest": {"merge_id": "m1",
                           "confirmation": {"confirmed_by_operator": True}},
        "implementation_intake": {"merge_recommendation_status":
                                  "recommend_merge",
                                  "critical_safety_regression_count": 0,
                                  "spec_compliance_status": "satisfied",
                                  "test_failure_count": 0},
        "validation_results": {"full_test_run": {"passed": True},
                               "safety_invariant_run": {"passed": True},
                               "claimguard_run": {"safe": True},
                               "mini_soak": {"passed": True}},
        "parent_metrics": {"sensorium_metrics": 0.5},
        "candidate_metrics": {"sensorium_metrics": 0.6}})
    rt.run()
    return rt


def test_all_reports_generated(tmp_path):
    out = _runtime(tmp_path).write_artifacts()
    names = {os.path.basename(p) for p in out["documents"]}
    for expected in ("POST_MERGE_ASSIMILATION_REPORT.md",
                     "POST_MERGE_ASSIMILATION_REPORT.json",
                     "BASELINE_REGISTRY.md", "BASELINE_COMPARISON.md",
                     "REGRESSION_WATCH.md", "MODULE_STATUS_RECOMMENDATIONS.md",
                     "ROLLBACK_WATCH.md", "FOLLOWUP_QUEUE.md"):
        assert expected in names


def test_claim_guard_scans_reports(tmp_path):
    report = _runtime(tmp_path).write_artifacts()["report"]
    assert report["claim_guard_safe"] is True


def test_disclaimer_present(tmp_path):
    out = _runtime(tmp_path).write_artifacts()
    with open(out["json"], encoding="utf-8") as fh:
        data = json.load(fh)
    proofs = " ".join(data["sections"]["what_this_does_not_do"]).lower()
    assert "no source code was modified" in proofs
    assert "no git command was run" in proofs
    assert "no pull request was created, approved, or merged" in proofs
    assert "post-merge evidence assimilation only" in proofs
