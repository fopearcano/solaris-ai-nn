#!/usr/bin/env python3
"""Research baseline demo: candidate baseline -> validation -> baseline report.

    python examples/run_research_baseline_snapshot_demo.py --state-dir .solaris_ai_nn_research_baseline/test_baseline

Turns a validated post-merge baseline into a local versioned research baseline:
a version record, validation summary, capability map, limitations, safety
boundary statement, comparison anchors, next-cycle roadmap, and operator runbook.
This is a local reproducible reference point, NOT a product or GitHub release.
(Distinct from the research-lab `run_research_baseline_demo.py`.)
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.research_baseline import ResearchBaselineRuntime


def main():
    parser = argparse.ArgumentParser(description="Research baseline demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_research_baseline/test_baseline")
    args = parser.parse_args()

    rt = ResearchBaselineRuntime(state_dir=args.state_dir,
                                 baseline_id="research_baseline_v1",
                                 parent_baseline_id="baseline_001")
    rt.load_bundle({
        "post_merge": {"candidate_baseline_status": "validated",
                       "candidate_baseline_id": "baseline_002",
                       "critical_regression_count": 0,
                       "baseline_regression_count": 0,
                       "rollback_recommendation_status": "no_rollback_needed",
                       "current_baseline_id": "baseline_001",
                       "unresolved_blockers": []},
        "implementation_intake": {"critical_safety_regression_count": 0,
                                  "coverage_gap_count": 0,
                                  "spec_compliance_status": "satisfied"},
        "validation_results": {"unit_tests": {"passed": True},
                               "integration_tests": {"passed": True},
                               "safety_tests": {"passed": True},
                               "claimguard": {"safe": True},
                               "safety_invariants": {"passed": True},
                               "example_runs": {"ran": True},
                               "mini_soak": {"passed": True},
                               "falsification_replay": {"passed": True},
                               "replication_registry": {"passed": True},
                               "documentation": {"passed": True}},
        "safety_artifacts": {"passed": True},
        "snapshot_artifacts": {
            "post_merge_assimilation_report": {"payload": {"x": 1}},
            "replication_report": {"payload": {"r": 1}},
            "falsification_report": {"payload": {"f": 1}},
            "soak_dossier": {"payload": {"s": 1}},
            "evaluation_report": {"payload": {"e": 1}}},
        "available_anchors": {"parent_baseline": "baseline_001",
                             "passive_parser_baseline": "ctrl_pp",
                             "fixture_only_baseline": "ctrl_fx"}})
    rt.run()
    out = rt.write_artifacts()
    st = rt.research_baseline_status()

    print("=== Research baseline demo ===")
    print(f"baseline version      : {st['current_baseline_version_id']} -> "
          f"{st['baseline_status']}")
    print(f"capabilities          : {st['capability_count']} "
          f"(validated {st['validated_capability_count']})")
    print(f"limitations           : {st['limitation_count']} "
          f"(critical {st['critical_limitation_count']})")
    print(f"safety boundary       : {st['safety_boundary_status']}")
    print(f"validation            : {st['validation_status']} "
          f"(pass {st['validation_pass_count']}, missing "
          f"{st['validation_missing_count']})")
    print(f"comparison anchors    : {st['comparison_anchor_count']}")
    print(f"next-cycle roadmap    : {st['roadmap_item_count']} item(s)")
    print(f"is git tag            : {st['is_git_tag']}  is release: "
          f"{st['is_github_release']}")
    print(f"report                : {out['markdown']}")
    print(f"documents             : {len(out['documents'])}")
    print("note                  : a research baseline is a local reproducible "
          "reference point; it creates no Git tag, GitHub release, branch, or "
          "PR, and makes no consciousness/life/agency claim.")


if __name__ == "__main__":
    main()
