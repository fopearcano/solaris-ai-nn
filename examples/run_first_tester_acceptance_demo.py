#!/usr/bin/env python3
"""First tester acceptance demo: criteria with pass/warning/blocker states.

    python examples/run_first_tester_acceptance_demo.py \\
        --tester-state-dir .solaris_ai_nn_tester/test_first_tester_acceptance

Generates the acceptance criteria and prints the categories and the result states a tester
or developer uses to judge each criterion (pass / warning / blocker).
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.first_tester_protocol import (
    AcceptanceResult,
    FirstTesterAcceptanceCriteria,
    FirstTesterProtocolRuntime,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/test_first_tester_acceptance")
    args = ap.parse_args()

    rt = FirstTesterProtocolRuntime(tester_state_dir=args.tester_state_dir,
                                    profile="first_tester_acceptance_only_v0",
                                    max_runtime_s=60.0)
    rt.run()
    d = FirstTesterAcceptanceCriteria().to_dict()
    print("first tester acceptance demo")
    print(f"  criteria      : {d['criterion_count']}")
    print(f"  result states : {AcceptanceResult.ALL}")
    print("  categories    :")
    for cat, n in d["categories"].items():
        print(f"    - {cat}: {n}")
    print(f"  acceptance doc: {rt.doc_paths.get('acceptance_criteria')}")
    print("note: acceptance criteria describe operational success, not "
          "cognition; no consciousness/life/agency claim.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
