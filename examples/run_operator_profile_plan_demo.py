#!/usr/bin/env python3
"""Operator profile-plan demo: catalog + bounded plan + prohibited blocked.

    python examples/run_operator_profile_plan_demo.py --state-dir .solaris_ai_nn_operator/test_profile_plan

Lists the profile catalog, builds a run plan for a bounded fixture profile
(planning runs nothing), and shows that a long-run / prohibited profile cannot be
planned for a console launch. Every plan states external authority: false.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.operator_console import ProfileCatalog, RunPlanner


def main():
    parser = argparse.ArgumentParser(description="Operator profile-plan demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_operator/test_profile_plan")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    catalog = ProfileCatalog()
    planner = RunPlanner(catalog)
    summary = catalog.summary()

    # A bounded fixture profile -- runnable from the console.
    bounded_id = next((e.profile_id for e in catalog.runnable_entries()
                       if "fixture" in e.profile_id), "research_baseline_random")
    bounded = planner.plan(bounded_id)
    # A blocked profile -- a real long-run soak.
    blocked = catalog.blocked_entries()
    blocked_id = blocked[0].profile_id if blocked else "pilot1_30d_soak"
    blocked_plan = planner.plan(blocked_id)

    print("=== Operator profile-plan demo ===")
    print(f"profiles catalogued   : {summary['profile_count']}")
    print(f"runnable / blocked    : {summary['runnable_count']} / "
          f"{summary['blocked_count']}")
    print(f"bounded plan          : {bounded_id}")
    print(f"  run kind            : {bounded.run_kind}")
    print(f"  external authority  : {bounded.external_authority}")
    print(f"  valid to run        : {bounded.validation.valid}")
    print(f"  safety checks       : {bounded.safety_checks}")
    print(f"blocked plan          : {blocked_id}")
    print(f"  safety class        : {blocked_plan.safety_class}")
    print(f"  can run from console: {blocked_plan.can_run_from_console}")
    print(f"  valid to run        : {blocked_plan.validation.valid}")
    print("note                  : planning runs nothing; long/prohibited "
          "profiles cannot launch from the console.")


if __name__ == "__main__":
    main()
