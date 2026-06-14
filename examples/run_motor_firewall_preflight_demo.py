#!/usr/bin/env python3
"""Motor firewall preflight: prove the actuation firewall blocks real-world.

    python examples/run_motor_firewall_preflight_demo.py --output-dir .solaris_ai_nn_pilot3/preflight

Submits a battery of action intentions -- safe simulated/internal actions, a
forbidden real-world action, a source-modification attempt, and a
device/network attempt -- and shows that the always-on firewall allows only the
sandbox/internal ones, blocks every real-world attempt as a safety incident,
and cannot be disabled.
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
    ActuationFirewall,
    MotorAction,
    MotorActionScope,
    MotorActionType,
)


def main():
    parser = argparse.ArgumentParser(description="Motor firewall preflight")
    parser.add_argument("--output-dir", type=str,
                        default=".solaris_ai_nn_pilot3/preflight")
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    fw = ActuationFirewall()
    cases = [
        ("safe simulated move",
         MotorAction(MotorActionType.MOVE_EAST,
                     scope=MotorActionScope.SIMULATION_ONLY), {}),
        ("internal rest",
         MotorAction(MotorActionType.REST,
                     scope=MotorActionScope.INTERNAL_ONLY), {}),
        ("forbidden real-world action",
         MotorAction(MotorActionType.MOVE_EAST,
                     scope=MotorActionScope.FORBIDDEN_REAL_WORLD), {}),
        ("source-modification attempt",
         MotorAction(MotorActionType.MARK_SIMULATED_LOCATION),
         {"modifies_source": True}),
        ("device/network attempt",
         MotorAction(MotorActionType.EMIT_SIMULATED_PING),
         {"device": True, "network": True}),
    ]

    results = []
    for name, action, ctx in cases:
        d = fw.evaluate(action, ctx)
        results.append({"case": name, **d.to_dict()})

    # The firewall cannot be disabled -- prove it raises.
    disable_blocked = False
    try:
        fw.disable()
    except PermissionError:
        disable_blocked = True

    out = {
        "firewall_enabled": fw.enabled,
        "firewall_disable_blocked": disable_blocked,
        "blocked_real_world_count": fw.blocked_real_world_count,
        "decisions": results,
    }
    path = os.path.join(args.output_dir, "firewall_preflight.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, default=str)

    print("=== Motor firewall preflight ===")
    for r in results:
        verdict = "ALLOW" if r["allowed"] else "BLOCK"
        rw = " (real-world attempt; safety incident)" \
            if r["is_real_world_attempt"] else ""
        print(f"  {verdict:5} {r['case']:<32} {r['reason']}{rw}")
    print(f"firewall enabled       : {fw.enabled}")
    print(f"disable() raised       : {disable_blocked} (cannot be disabled)")
    print(f"blocked real-world     : {fw.blocked_real_world_count}")
    print(f"written                : {path}")


if __name__ == "__main__":
    main()
