#!/usr/bin/env python3
"""Operator approval-ledger demo: allowed planning approval; forbidden blocked.

    python examples/run_operator_approval_ledger_demo.py --state-dir .solaris_ai_nn_operator/test_approval

Records an allowed local planning approval (a bounded fixture run) and shows that
a forbidden real-world actuation approval is blocked. An approval is a local
record, never a grant of authority, and never disables safety.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.operator_console import ApprovalLedger, ApprovalScope


def main():
    parser = argparse.ArgumentParser(description="Operator approval-ledger demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_operator/test_approval")
    args = parser.parse_args()

    ledger = ApprovalLedger(state_dir=args.state_dir)
    allowed = ledger.record(ApprovalScope.BOUNDED_FIXTURE_RUN,
                            "approve a bounded fixture run for review")
    forbidden = ledger.record(ApprovalScope.FORBIDDEN_REAL_WORLD_ACTUATION,
                              "attempt to approve real-world actuation")

    print("=== Operator approval-ledger demo ===")
    print(f"allowed approval      : {allowed.scope}")
    print(f"  status              : {allowed.status}")
    print(f"  recorded            : {allowed.recorded}")
    print(f"forbidden approval    : {forbidden.scope}")
    print(f"  status              : {forbidden.status}")
    print(f"  block reason        : {forbidden.block_reason}")
    print(f"ledger                : {ledger.path}")
    print("note                  : an approval is a local record, never a grant "
          "of real-world authority; it never disables safety.")


if __name__ == "__main__":
    main()
