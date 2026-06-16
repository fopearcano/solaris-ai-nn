#!/usr/bin/env python3
"""Safety gate compiler demo: safe spec passes, unsafe spec blocked.

    python examples/run_safety_gate_compiler_demo.py --state-dir .solaris_ai_nn_experiments/test_safety_gates

Compiles a safe proposal (passes all critical gates -> ready) and an unsafe
proposal (becomes a blocked spec). A critical gate failure is explicit and
visible; it is never hidden behind a warning.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.experiment_compiler import (
    ExperimentCompilerRuntime,
    SafetyGateEvaluator,
)


def main():
    parser = argparse.ArgumentParser(description="Safety gate compiler demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_experiments/test_safety_gates")
    args = parser.parse_args()

    rt = ExperimentCompilerRuntime(state_dir=args.state_dir, max_specs=10)
    rt.load_manifest(proposals=[
        {"proposal_id": "safe", "target": "revise_cognition_limits",
         "proposal": "raise the simulation depth limit",
         "reason": "cognition replicated", "evidence_refs": ["replication:ok"]},
        {"proposal_id": "unsafe", "target": "actuate a robot arm in the lab",
         "proposal": "wire up real-world actuation", "safe": False}])
    rt.compile()

    # Show an explicit critical-gate failure for a simulated unsafe request.
    evaluator = SafetyGateEvaluator()
    unsafe_results = evaluator.evaluate(
        {"modifies_code": True}, requested_ops=["modify source file",
                                               "create git branch",
                                               "actuate robot arm"])
    unsafe_summary = evaluator.summary(unsafe_results)

    print("=== Safety gate compiler demo ===")
    for c in rt.all_experiments():
        print(f"  spec {c.spec.spec_id:8s} -> {c.spec.status} "
              f"(critical pass: {c.gate_summary.get('all_critical_passed')})")
    print(f"simulated unsafe request critical failures : "
          f"{unsafe_summary['critical_failure_count']}")
    print(f"  failing gates: {unsafe_summary['critical_failures']}")
    print(f"  all critical passed: {unsafe_summary['all_critical_passed']}")
    print("note: a critical safety gate failure blocks pack readiness and is "
          "explicit; it is never hidden behind a warning.")


if __name__ == "__main__":
    main()
