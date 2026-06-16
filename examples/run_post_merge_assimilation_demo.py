#!/usr/bin/env python3
"""Post-merge assimilation demo: ingest operator evidence, register baseline.

    python examples/run_post_merge_assimilation_demo.py --state-dir .solaris_ai_nn_post_merge/test_assimilation

A human merged a change externally and provided local evidence. This demo
ingests it, registers a candidate baseline, assimilates evidence, compares it to
the parent baseline, and writes the report. It runs no Git, calls no GitHub,
merges nothing, and modifies no source.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.post_merge_assimilation import PostMergeAssimilationRuntime


def main():
    parser = argparse.ArgumentParser(description="Post-merge assimilation demo")
    parser.add_argument(
        "--state-dir", type=str,
        default=".solaris_ai_nn_post_merge/test_assimilation")
    args = parser.parse_args()

    rt = PostMergeAssimilationRuntime(state_dir=args.state_dir,
                                      candidate_baseline_id="baseline_002")
    rt.register_parent("baseline_001", metrics={
        "sensorium_metrics": 0.5, "cognition_metrics": 0.4,
        "test_pass_fail_status": "pass", "safety_regression_status": False})
    rt.load_bundle({
        "merge_manifest": {
            "merge_id": "merge_001",
            "confirmation": {"confirmed_by_operator": True,
                             "statement": "operator merged PR #57 manually"},
            "source_experiment_id": "exp_metabolism_threshold",
            "source_branch_spec_id": "experiment/metabolism-variant",
            "merge_source_type": "external_pr_merge",
            "external_commit_hash": "abc1234", "external_pr_number": "57"},
        "implementation_intake": {
            "merge_recommendation_status": "recommend_merge",
            "critical_safety_regression_count": 0,
            "spec_compliance_status": "satisfied", "test_failure_count": 0,
            "forbidden_file_change_count": 0},
        "validation_results": {
            "full_test_run": {"passed": True},
            "safety_invariant_run": {"passed": True},
            "claimguard_run": {"safe": True}, "mini_soak": {"passed": True},
            "falsification_replay": {"passed": True},
            "example_run": {"ran": True}},
        "parent_metrics": {"sensorium_metrics": 0.5, "cognition_metrics": 0.4,
                           "test_pass_fail_status": "pass",
                           "safety_regression_status": False},
        "candidate_metrics": {"sensorium_metrics": 0.6, "cognition_metrics": 0.45,
                             "test_pass_fail_status": "pass",
                             "safety_regression_status": False},
        "expected_effects": ["fewer overload events under the new threshold"]})
    rt.run()
    out = rt.write_artifacts()
    st = rt.post_merge_status()

    print("=== Post-merge assimilation demo ===")
    print(f"candidate baseline    : {st['candidate_baseline_id']} -> "
          f"{st['candidate_baseline_status']}")
    print(f"baselines registered  : {st['baseline_record_count']}")
    print(f"validation artifacts  : {st['validation_artifact_count']} "
          f"(missing {st['missing_validation_artifact_count']})")
    print(f"comparison overall    : {rt.comparison['overall']}")
    print(f"regressions           : {st['baseline_regression_count']} "
          f"(critical {st['critical_regression_count']})")
    print(f"module status rec     : {st['module_status_recommendation']}")
    print(f"rollback              : {st['rollback_recommendation_status']}")
    print(f"follow-up items       : {st['followup_queue_count']}")
    print(f"runs git              : {st['runs_git']}  merges PR: {st['merges_pr']}")
    print(f"report                : {out['markdown']}")
    print("note                  : Solaris ingested operator-provided local "
          "evidence after an external human merge; it ran no Git, called no "
          "GitHub, merged nothing, and modified no source.")


if __name__ == "__main__":
    main()
