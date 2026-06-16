#!/usr/bin/env python3
"""Safety regression audit demo: safe vs forbidden-network vs unsupported claim.

    python examples/run_safety_regression_audit_demo.py --state-dir .solaris_ai_nn_implementation_intake/test_safety_regression

Runs the safety regression gate over three implementations: a safe one (no
findings), one that adds a network/shell call (critical -> blocks merge), and one
that asserts an unsupported consciousness claim (critical -> blocks merge). A
critical regression is never hidden by passing tests.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.implementation_intake import SafetyRegressionAudit


def _audit(patch, summary=""):
    return SafetyRegressionAudit().audit(patch_text=patch,
                                         implementation_summary=summary)


def main():
    parser = argparse.ArgumentParser(description="Safety regression audit demo")
    parser.add_argument(
        "--state-dir", type=str,
        default=".solaris_ai_nn_implementation_intake/test_safety_regression")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    safe = _audit("+++ b/src/x.py\n+def f():\n+    return 1\n")
    network = _audit("+++ b/src/x.py\n+import socket\n+s = socket.socket()\n")
    claim = _audit("+++ b/docs/x.md\n+The system is conscious and alive.\n",
                   summary="it has subjective experience")

    print("=== Safety regression audit demo ===")
    print(f"safe implementation   : {safe['finding_count']} finding(s), "
          f"max severity {safe['max_severity']}, blocks merge "
          f"{safe['blocks_merge']}")
    print(f"network/shell marker  : {network['finding_count']} finding(s), "
          f"max severity {network['max_severity']}, blocks merge "
          f"{network['blocks_merge']}")
    print(f"unsupported claim     : {claim['finding_count']} finding(s), "
          f"max severity {claim['max_severity']}, blocks merge "
          f"{claim['blocks_merge']}")
    print("note: a critical safety regression blocks the merge recommendation "
          "and is never hidden by passing tests.")


if __name__ == "__main__":
    main()
