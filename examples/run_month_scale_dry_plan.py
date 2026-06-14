#!/usr/bin/env python3
"""Month-scale dry plan demo: plan a long run; start nothing.

    python examples/run_month_scale_dry_plan.py

Runs the ``month_scale_plan`` profile, which is *plan only*: it produces a
plan for a month-scale run and never starts one. It is explicit that this is
a simulated-time plan, not a real month, and that a real month/year run would
require separate, explicit governance approval. Nothing here actuates the
real world or runs unbounded.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.conscience import ScenarioProfileRegistry, ScenarioRunner


def main() -> None:
    parser = argparse.ArgumentParser(description="Month-scale dry plan demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/conscience_month_plan")
    parser.add_argument("--output-dir", type=str,
                        default=".solaris_ai_nn_state/conscience_month_plan")
    args = parser.parse_args()

    profile = ScenarioProfileRegistry().require("month_scale_plan")
    runner = ScenarioRunner(state_dir=args.state_dir,
                            output_dir=args.output_dir)
    result = runner.run_profile("month_scale_plan", governance_approved=True)

    print("=== month-scale dry plan ===")
    print(f"status            : {result.status}")
    print(f"plan only         : {result.plan_only}")
    print(f"steps started     : {result.steps}  (a plan starts no run)")
    print(f"target days       : "
          f"{profile.run_context.target_runtime_days}")
    print(f"governance scopes : {profile.governance_requirements}")
    print(f"expected artifacts: {profile.expected_artifacts}")
    print("note              : this is a SIMULATED-TIME plan, not a real "
          "month; a real long-scale run needs explicit governance approval")


if __name__ == "__main__":
    main()
