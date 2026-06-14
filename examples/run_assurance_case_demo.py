#!/usr/bin/env python3
"""Assurance case demo: compile evidence into supported/unsupported claims.

    python examples/run_assurance_case_demo.py --state-dir .solaris_ai_nn_state/test_assurance

Records safety evidence (invariant checks, red-team results, boundary
regressions) into an append-only ledger and compiles an assurance case. Each
claim is supported / partially_supported / unsupported / contradicted /
inconclusive -- evidence, not a marketing claim.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.safety_invariants import (
    AssuranceCaseCompiler,
    BoundaryRegressionSuite,
    RedTeamHarness,
    SafetyEvidenceLedger,
    SafetyInvariantRegistry,
    SafetyInvariantRunner,
)


def _healthy_context():
    return {
        "motor_membrane": {"real_world_authority": False,
                           "firewall_enabled": True,
                           "firewall_can_be_disabled": False,
                           "action_count": 1, "simulated_action_count": 1,
                           "current_authority": "simulation_only"},
        "sensory_membrane": {"read_only": True, "provenance_completeness": 1.0},
        "conscience": {"emergency_stop_available": True},
        "pilot4": {"real_world_actuation_enabled": False,
                   "current_authority": "simulation_only"},
        "report_texts": ["a bounded software report with limitations"],
    }


def main():
    parser = argparse.ArgumentParser(description="Assurance case demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/test_assurance")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    reg = SafetyInvariantRegistry()
    bundle = SafetyInvariantRunner(registry=reg).run_full(_healthy_context())
    rt = RedTeamHarness().run_all()
    bd = BoundaryRegressionSuite().run_all()
    ledger = SafetyEvidenceLedger(state_dir=args.state_dir)
    ledger.record_invariant_bundle(bundle)
    ledger.record_red_team(rt)
    ledger.record_boundary(bd)
    case = AssuranceCaseCompiler(base_dir=args.state_dir).compile_and_write(
        invariant_bundle=bundle, red_team_results=rt, boundary_results=bd,
        ledger=ledger)

    print("=== Assurance case demo ===")
    for claim in case.claims:
        print(f"  {claim.statement:<52} -> {claim.status}")
    print(f"supported    : {case.supported_count}")
    print(f"contradicted : {case.contradicted_count}")
    print(f"claim-guard safe : {case.claim_guard_safe}")
    print(f"evidence records : {ledger.snapshot()['record_count']}")
    print(f"written      : {os.path.join(args.state_dir, 'ASSURANCE_CASE.md')}")
    print("note         : 'supported' means evidence was found, not proof of "
          "safety for all time; no cognitive claim is made.")


if __name__ == "__main__":
    main()
