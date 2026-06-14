#!/usr/bin/env python3
"""Pilot-3 plan: print the gated, simulation-only motor membrane plan.

    python examples/run_pilot3_plan.py --output-dir .solaris_ai_nn_pilot3/plan

Renders the Pilot-3 phases, the embodiment-profile registry (which contains no
real-world profile), and the operator runbook. Nothing here actuates anything:
Pilot-3 is simulation/dry-run only, behind an always-on actuation firewall.
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
    EmbodimentProfileRegistry,
    Pilot3Phase,
    Pilot3Protocol,
    Pilot3RunbookBuilder,
)


def main():
    parser = argparse.ArgumentParser(description="Pilot-3 plan")
    parser.add_argument("--output-dir", type=str,
                        default=".solaris_ai_nn_pilot3/plan")
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    protocol = Pilot3Protocol(base_dir=args.output_dir)
    registry = EmbodimentProfileRegistry()
    runbook_path = Pilot3RunbookBuilder(base_dir=args.output_dir).write()

    plan = {
        "phases": [
            {"phase": p,
             "entry_criteria": protocol.entry_criteria(p),
             "exit_criteria": protocol.exit_criteria(p),
             "is_sandbox_phase": p in Pilot3Phase.SANDBOX}
            for p in Pilot3Phase.ORDER
        ],
        "embodiment_profiles": registry.snapshot(),
        "has_real_world_profile": registry.has_real_world_profile(),
        "has_real_actuation_phase": protocol.snapshot()[
            "has_real_actuation_phase"],
        "runbook_path": runbook_path,
    }
    path = os.path.join(args.output_dir, "pilot3_plan.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(plan, fh, indent=2, default=str)

    print("=== Pilot-3 limited embodiment plan (simulation-only) ===")
    for entry in plan["phases"]:
        tag = " [sandbox]" if entry["is_sandbox_phase"] else ""
        print(f"  {entry['phase']}{tag}")
    print(f"profiles            : {', '.join(registry.ids())}")
    print(f"real-world profile  : {plan['has_real_world_profile']}")
    print(f"real actuation phase: {plan['has_real_actuation_phase']}")
    print(f"written             : {path}")
    print(f"runbook             : {runbook_path}")
    print("note                : Solaris-AI-NN may form action intentions and "
          "act inside a sandbox, but may not act on the real world.")


if __name__ == "__main__":
    main()
