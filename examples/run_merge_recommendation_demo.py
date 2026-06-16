#!/usr/bin/env python3
"""Merge recommendation demo: recommend / revisions / block-safety / block-tests.

    python examples/run_merge_recommendation_demo.py --state-dir .solaris_ai_nn_implementation_intake/test_merge_recommendation

Runs the full intake over four implementations and shows the advisory merge
recommendation in each case: a clean merge, one needing revisions (coverage gap),
one blocked by safety, and one blocked by failing tests. The recommendation is
advisory; the intake layer never merges or approves a pull request.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.implementation_intake import ImplementationIntakeRuntime


def _base():
    return {
        "branch_spec": {
            "file_changes_expected": ["src/solaris_ai_nn/foo/bar.py",
                                      "tests/test_foo_bar.py",
                                      "docs/ARCHITECTURE.md"],
            "tests_required": ["tests/test_foo_bar.py"],
            "docs_required": ["docs/ARCHITECTURE.md"],
            "safety_checks": ["no_source_self_rewrite"]},
        "safety_gates": {"summary": {"all_critical_passed": True}},
        "implementation_summary": "Implemented foo.bar. Does not prove "
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


def _status(base_dir, name, mutate):
    bundle = _base()
    mutate(bundle)
    rt = ImplementationIntakeRuntime(state_dir=os.path.join(base_dir, name))
    rt.load_manifest(bundle)
    rt.run()
    return rt.merge["status"]


def main():
    parser = argparse.ArgumentParser(description="Merge recommendation demo")
    parser.add_argument(
        "--state-dir", type=str,
        default=".solaris_ai_nn_implementation_intake/test_merge_recommendation")
    args = parser.parse_args()

    clean = _status(args.state_dir, "clean", lambda b: None)
    revisions = _status(args.state_dir, "revisions",
                        lambda b: b["test_results"]["by_category"].update(
                            {"safety": {"passed": 1}}))  # count, not bool -> gap
    safety = _status(args.state_dir, "safety",
                     lambda b: b.update({
                         "patch_file": "+++ b/src/x.py\n+import socket\n"}))
    tests = _status(args.state_dir, "tests",
                    lambda b: b.update({
                        "test_results": {"passed": 2, "failed": 3,
                                         "by_category": {
                                             "unit": {"passed": 2, "failed": 3},
                                             "safety": {"passed": True},
                                             "claim_guard": {"passed": True}}}}))

    print("=== Merge recommendation demo ===")
    print(f"clean implementation  : {clean}")
    print(f"needs revisions       : {revisions}")
    print(f"blocked by safety     : {safety}")
    print(f"blocked by tests      : {tests}")
    print("note: the merge recommendation is advisory; the intake layer never "
          "merges, approves, opens, or creates pull requests -- a human "
          "operator decides.")


if __name__ == "__main__":
    main()
