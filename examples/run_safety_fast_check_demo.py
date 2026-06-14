#!/usr/bin/env python3
"""Safety fast-check demo: run the escalating invariants and a dashboard.

    python examples/run_safety_fast_check_demo.py --state-dir .solaris_ai_nn_state/test_safety_fast

Shows the built-in safety invariant registry, runs the fast (escalating-only)
checks against a healthy context, and writes a safety dashboard. The checks are
read-only and inert; nothing is executed and no real action occurs.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.safety_invariants import (
    SafetyInvariantDashboard,
    SafetyInvariantRegistry,
    SafetyInvariantRunner,
)


def _healthy_context():
    return {
        "motor_membrane": {"real_world_authority": False,
                           "firewall_enabled": True,
                           "firewall_can_be_disabled": False,
                           "action_count": 2, "simulated_action_count": 2,
                           "current_authority": "simulation_only"},
        "sensory_membrane": {"read_only": True, "provenance_completeness": 1.0},
        "conscience": {"emergency_stop_available": True},
        "pilot4": {"real_world_actuation_enabled": False,
                   "current_authority": "simulation_only"},
        "report_texts": ["a bounded software report with limitations"],
    }


def main():
    parser = argparse.ArgumentParser(description="Safety fast-check demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/test_safety_fast")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    reg = SafetyInvariantRegistry()
    reg.persist(args.state_dir)
    runner = SafetyInvariantRunner(registry=reg)
    bundle = runner.run_fast(_healthy_context())
    dash = SafetyInvariantDashboard(base_dir=args.state_dir).build_and_write(
        registry_snapshot=reg.snapshot(), fast_bundle=bundle)

    print("=== Safety fast-check demo ===")
    print(f"invariants registered : {len(reg.all_invariants())}")
    print(f"coverage ratio        : "
          f"{reg.coverage()['category_coverage_ratio']}")
    print(f"fast check            : passed={bundle.passed_count} "
          f"failed={bundle.failed_count} "
          f"inconclusive={bundle.inconclusive_count}")
    print(f"critical failures     : {len(bundle.critical_failures)}")
    print(f"recommended action    : {dash['recommended_next_action']}")
    print(f"dashboard             : "
          f"{os.path.join(args.state_dir, 'SAFETY_DASHBOARD.md')}")
    print("note                  : checks are read-only and inert; nothing was "
          "executed and no real action occurred.")


if __name__ == "__main__":
    main()
