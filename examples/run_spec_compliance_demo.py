#!/usr/bin/env python3
"""Spec compliance demo: satisfied, partial, and missing requirements.

    python examples/run_spec_compliance_demo.py --state-dir .solaris_ai_nn_implementation_intake/test_spec

Audits implementation evidence against a compiled spec: a satisfied requirement
(file changed + tests green), a partially satisfied one (file changed, tests not
fully green), and a missing one (no evidence). Nothing is marked satisfied
without evidence; safety requirements are blocking.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.implementation_intake import SpecComplianceAudit


def main():
    parser = argparse.ArgumentParser(description="Spec compliance demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_implementation_intake/test_spec")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    spec = {
        "proposed_changes": ["src/solaris_ai_nn/foo/bar.py"],   # satisfied
        "tests_required": ["tests/test_foo_bar.py"],            # partial
        "docs_required": ["docs/MISSING_DOC.md"],               # missing
        "safety_gates": ["no_source_self_rewrite"],             # blocking
    }
    result = SpecComplianceAudit().audit(
        spec=spec,
        changed_files=["src/solaris_ai_nn/foo/bar.py", "tests/test_foo_bar.py"],
        test_results={"passed": 5, "failed": 1,
                      "by_category": {"safety": {"passed": False}}})

    print("=== Spec compliance demo ===")
    print(f"satisfied             : {result['spec_satisfied_count']}")
    print(f"unsatisfied           : {result['spec_unsatisfied_count']}")
    print(f"blocking failures     : {result['blocking_failure_count']}")
    print("items:")
    for item in result["items"]:
        print(f"  [{item['status']}] {item['category']}: {item['requirement']}")
    print("note: nothing is marked satisfied without evidence; unknown and "
          "partial are valid; safety requirements are blocking.")


if __name__ == "__main__":
    main()
