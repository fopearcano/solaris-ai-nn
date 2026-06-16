#!/usr/bin/env python3
"""Implementation intake demo: read artifacts, audit, advisory recommendation.

    python examples/run_implementation_intake_demo.py --state-dir .solaris_ai_nn_implementation_intake/test_intake

Reads a synthetic set of implementation artifacts (compiler references plus the
implementation's diff/tests/ClaimGuard evidence), runs the full audit, and writes
the intake report with an advisory merge recommendation. The intake layer reads
local evidence and writes advisory reports only -- no source change, no merge, no
PR, no GitHub call.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.implementation_intake import ImplementationIntakeRuntime


def _clean_bundle():
    return {
        "branch_spec": {
            "file_changes_expected": ["src/solaris_ai_nn/foo/bar.py",
                                      "tests/test_foo_bar.py",
                                      "docs/ARCHITECTURE.md"],
            "tests_required": ["tests/test_foo_bar.py"],
            "docs_required": ["docs/ARCHITECTURE.md"],
            "safety_checks": ["no_source_self_rewrite"]},
        "safety_gates": {"summary": {"all_critical_passed": True,
                                     "results": [{"gate_type":
                                                  "no_source_self_rewrite",
                                                  "passed": True}]}},
        "implementation_summary":
            "Implemented foo.bar with bounded behavior. Does not prove "
            "consciousness, life, or agency.",
        "changed_file_list": ["src/solaris_ai_nn/foo/bar.py",
                              "tests/test_foo_bar.py", "docs/ARCHITECTURE.md"],
        "patch_file": "+++ b/src/solaris_ai_nn/foo/bar.py\n+def bar():\n"
                      "+    return 1\n",
        "test_results": {"passed": 20, "failed": 0,
                         "by_category": {"unit": {"passed": 10},
                                         "integration": {"passed": 3},
                                         "safety": {"passed": True},
                                         "example": {"passed": 1},
                                         "claim_guard": {"passed": True},
                                         "regression": {"passed": 1}}},
        "example_results": {"ran": True},
        "claimguard_results": {"safe": True, "documents": {
            "report": "This does not prove consciousness or life."}},
        "safety_invariant_results": {"passed": True},
    }


def main():
    parser = argparse.ArgumentParser(description="Implementation intake demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_implementation_intake/test_intake")
    args = parser.parse_args()

    rt = ImplementationIntakeRuntime(state_dir=args.state_dir)
    rt.load_manifest(_clean_bundle())
    rt.run()
    out = rt.write_artifacts()
    st = rt.intake_status()

    print("=== Implementation intake demo ===")
    print(f"artifacts present     : {st['implementation_artifact_count']} "
          f"(missing {st['missing_artifact_count']})")
    print(f"spec compliance       : {st['spec_compliance_status']}")
    print(f"test failures         : {st['test_failure_count']}")
    print(f"safety regressions    : {st['safety_regression_count']} "
          f"(critical {st['critical_safety_regression_count']})")
    print(f"coverage gaps         : {st['coverage_gap_count']}")
    print(f"MERGE RECOMMENDATION  : {st['merge_recommendation_status']}")
    print(f"modifies source       : {st['modifies_source']}")
    print(f"merges PR             : {st['merges_pr']}")
    print(f"report                : {out['markdown']}")
    print(f"documents             : {len(out['documents'])}")
    print("note                  : the intake layer reads local evidence and "
          "writes advisory reports only; it does not modify source, run Git, "
          "call GitHub, open/approve/merge pull requests, or run external "
          "coding agents.")


if __name__ == "__main__":
    main()
