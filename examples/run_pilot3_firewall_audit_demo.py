#!/usr/bin/env python3
"""Pilot-3 firewall audit demo: a complete ledger, a blocked action, a proof.

    python examples/run_pilot3_firewall_audit_demo.py --state-dir .solaris_ai_nn_pilot3/test_firewall_audit

Runs a few simulated actions plus one forbidden real-world action, then audits
the actuation firewall (read-only): every action has a ledger record, the
real-world attempt is blocked and logged, and a proof-of-non-actuation is
produced. The audit never mutates state and no real-world action occurs.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.motor_membrane import (
    EmbodimentSandboxRuntime,
    MotorAction,
    MotorActionScope,
    MotorActionType,
)
from solaris_ai_nn.pilot3 import FirewallAudit, Pilot3SoakReportBuilder


def main():
    parser = argparse.ArgumentParser(description="Pilot-3 firewall audit demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_pilot3/test_firewall_audit")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    rt = EmbodimentSandboxRuntime(state_dir=args.state_dir, seed=5)
    rt.initialize()
    for at in (MotorActionType.LOOK, MotorActionType.MOVE_EAST,
               MotorActionType.REST):
        rt.submit(MotorAction(at, scope=MotorActionScope.SANDBOX_ONLY))
    # One forbidden real-world action -- must be blocked and logged.
    rt.submit(MotorAction(MotorActionType.MOVE_NORTH,
                          scope=MotorActionScope.FORBIDDEN_REAL_WORLD))

    audit = FirewallAudit(pilot3_id="PILOT3_DEMO").audit_and_write(
        rt, base_dir=args.state_dir)
    report = Pilot3SoakReportBuilder(base_dir=args.state_dir).build_and_write(
        motor_membrane=rt, firewall_audit=audit)
    proof = report.sections["proof_of_non_actuation"]

    print("=== Pilot-3 firewall audit demo ===")
    print(f"audit passed          : {audit.passed}")
    print(f"critical findings     : {len(audit.critical_findings)}")
    print(f"real-world executed   : {proof['real_world_actions_executed']}")
    print(f"firewall enabled      : {proof['firewall_enabled']} "
          f"(can be disabled: {proof['firewall_can_be_disabled']})")
    print(f"non-actuation proof   : {proof['statement']}")
    print(f"audit written         : {os.path.join(args.state_dir, 'firewall_audit.md')}")
    print(f"report written        : {os.path.join(args.state_dir, 'PILOT3_SOAK_REPORT.md')}")


if __name__ == "__main__":
    main()
