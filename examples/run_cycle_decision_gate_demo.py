#!/usr/bin/env python3
"""Cycle decision gate demo: advisory gates that never self-approve.

    python examples/run_cycle_decision_gate_demo.py

Evaluates the research-cycle decision gates for three cases: (1) a clean cycle
waiting on an operator merge confirmation, (2) the same cycle once the operator
has confirmed, and (3) a cycle with a critical safety regression. Promotion gates
are blocked by safety/falsification/regression; operator gates show
"waiting_for_operator" until an explicit operator decision exists; and Solaris
never auto-approves an operator gate.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.research_cycle import ResearchCycleDecisionGate


def _bundle(safety_ok=True):
    return {
        "research_baseline": {"baseline_status": "validated",
                              "safety_boundary_status": "pass"},
        "experiment_compiler": {"ready_spec_count": 3,
                                "safety_gate_failure_count": 0},
        "implementation_intake": {
            "merge_recommendation_status":
                "recommend" if safety_ok else "block_merge_due_to_safety",
            "critical_safety_regression_count": 0 if safety_ok else 1},
        "post_merge": {"candidate_baseline_status": "validated",
                       "critical_regression_count": 0},
        "falsification": {"falsified_claim_count": 0},
    }


def _show(label, bundle, decisions):
    gate = ResearchCycleDecisionGate()
    summary = gate.summary(gate.evaluate_all(bundle, operator_decisions=decisions))
    print(f"=== {label} ===")
    print(f"  gates {summary['decision_gate_count']}, passed "
          f"{summary['passed_count']}, failed "
          f"{summary['failed_decision_gate_count']}, waiting-for-operator "
          f"{summary['waiting_for_operator_count']}")
    for r in summary["results"]:
        op = " [operator decision required]" \
            if r["operator_decision_required"] else ""
        print(f"    - {r['gate_type']:28s} {r['status']}{op}")


def main():
    argparse.ArgumentParser(description="Cycle decision gate demo").parse_args()

    _show("Clean cycle, no operator decision yet", _bundle(), [])
    print()
    _show("Clean cycle, operator confirmed merge + baseline", _bundle(), [
        {"decision_type": "confirm_external_merge", "status": "approved"},
        {"decision_type": "approve_candidate_baseline", "status": "approved"},
        {"decision_type": "start_next_cycle", "status": "approved"}])
    print()
    _show("Critical safety regression at intake", _bundle(safety_ok=False), [
        {"decision_type": "confirm_external_merge", "status": "approved"}])
    print()
    print("note: gate results are advisory metadata. Operator gates cannot be "
          "auto-approved -- a gate stays 'waiting_for_operator' until an explicit "
          "local operator decision exists. A critical safety failure blocks the "
          "promotion gates regardless of any operator decision.")


if __name__ == "__main__":
    main()
