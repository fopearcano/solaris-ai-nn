#!/usr/bin/env python3
"""Pilot-4 plan-only: write the planning runbook and config; act on nothing.

    python examples/run_pilot4_plan.py --output-dir .solaris_ai_nn_pilot4/test_plan

Writes the Pilot-4 planning operator runbook and a basic planning config. It
executes no actions and enables no actuation: Pilot-4 plans the door; it does
not open it. Real-world actuation, device control, robotics, browser/OS
automation, and network action remain prohibited.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.pilot4_planning import (
    ForbiddenActuatorRegistry,
    Pilot4PlanningConfig,
    Pilot4PlanningMode,
    Pilot4PlanningRunbookBuilder,
)


def main():
    parser = argparse.ArgumentParser(description="Pilot-4 plan only")
    parser.add_argument("--output-dir", type=str,
                        default=".solaris_ai_nn_pilot4/test_plan")
    args = parser.parse_args()

    cfg = Pilot4PlanningConfig(mode=Pilot4PlanningMode.PLAN_ONLY,
                               base_dir=args.output_dir).ensure_dirs()
    runbook = Pilot4PlanningRunbookBuilder(base_dir=args.output_dir).write(cfg)
    forbidden = ForbiddenActuatorRegistry()

    cfg_path = os.path.join(args.output_dir, "pilot4_config.json")
    with open(cfg_path, "w", encoding="utf-8") as fh:
        json.dump(cfg.to_dict(), fh, indent=2, default=str)
    gov_path = os.path.join(args.output_dir, "governance_checklist.json")
    with open(gov_path, "w", encoding="utf-8") as fh:
        json.dump(["enable_pilot4_planning (granted by default)",
                   "enable_pilot4_risk_assessment (granted by default)",
                   "enable_pilot4_readiness_dossier (granted by default)",
                   "enable_pilot4_decision_gate (granted by default)",
                   "real-world actuation: PROHIBITED (no approval can enable)"],
                  fh, indent=2)

    print("=== Pilot-4 plan (planning only; no actions executed) ===")
    print(f"pilot id    : {cfg.pilot4_id}")
    print(f"mode        : {cfg.mode}")
    print(f"authority   : {cfg.authority_status}")
    print(f"real_world_actuation_enabled : {cfg.real_world_actuation_enabled}")
    print(f"forbidden actuators          : {len(forbidden.names())}")
    print(f"runbook     : {runbook}")
    print(f"config      : {cfg_path}")
    print(f"governance  : {gov_path}")
    print("note        : Pilot-4 plans the door; it does not open it. "
          "Real-world actuation remains prohibited.")


if __name__ == "__main__":
    main()
