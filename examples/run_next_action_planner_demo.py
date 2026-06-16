#!/usr/bin/env python3
"""Next action planner demo: instructions for the operator, never executed.

    python examples/run_next_action_planner_demo.py

Shows the recommended next operator action across several cycle stages, and the
blocker-resolution action when the cycle is blocked. Next actions are
instructions for the human operator; none is executed automatically; high-risk
actions carry safety context; and a critical safety blocker is flagged as one
that can never be bypassed.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.research_cycle import NextActionPlanner, ResearchCycleStage


def _show(label, **kwargs):
    summary = NextActionPlanner.summary(NextActionPlanner().plan(**kwargs))
    print(f"=== {label} ===")
    print(f"  executes automatically: {summary['executes_automatically']}")
    for a in summary["actions"]:
        ctx = f" [{a['safety_context']}]" if a.get("safety_context") else ""
        print(f"    - [{a['priority']}] {a['action_type']}: "
              f"{a['detail']}{ctx} (executed={a['executed']}, "
              f"for_operator={a['for_operator']})")


def main():
    argparse.ArgumentParser(description="Next action planner demo").parse_args()

    _show("Stage: experiment pack compiled (high-risk hand-off)",
          stage=ResearchCycleStage.EXPERIMENT_PACK_COMPILED, blocked=False)
    print()
    _show("Stage: implementation audited (human review)",
          stage=ResearchCycleStage.IMPLEMENTATION_AUDITED, blocked=False)
    print()
    _show("Stage: research baseline validated",
          stage=ResearchCycleStage.RESEARCH_BASELINE_VALIDATED, blocked=False)
    print()
    _show("Blocked: critical safety blocker", stage=ResearchCycleStage.BLOCKED,
          blocked=True, blocked_states=[
              {"reason": "safety_gate_failed", "critical_safety": True,
               "recommendation": "run_safety_audit"}])
    print()
    print("note: next actions are instructions for the human/operator; none is "
          "executed automatically. If the cycle is blocked, the next action is "
          "blocker resolution, and a critical safety blocker can never be "
          "bypassed.")


if __name__ == "__main__":
    main()
