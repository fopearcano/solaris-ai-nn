#!/usr/bin/env python3
"""Pilot-3 soak plan-only: write runbook, comparison design, governance list.

    python examples/run_pilot3_soak_plan.py --output-dir .solaris_ai_nn_pilot3/test_soak_plan

Generates the Pilot-3 simulated-embodiment soak operator runbook, a comparison
design (read-only vs simulated action vs mixed), and a governance checklist. It
starts no run and runs no actions: Pilot-3 is sandboxed action grounding, not
real embodiment, and an always-on actuation firewall blocks every real-world
effect.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.pilot3 import (
    Pilot3ComparativeDesign,
    Pilot3ComparisonArm,
    Pilot3Config,
    Pilot3Mode,
    Pilot3SoakRunbookBuilder,
)


def main():
    parser = argparse.ArgumentParser(description="Pilot-3 soak plan only")
    parser.add_argument("--output-dir", type=str,
                        default=".solaris_ai_nn_pilot3/test_soak_plan")
    args = parser.parse_args()

    cfg = Pilot3Config(mode=Pilot3Mode.PLAN_ONLY, base_dir=args.output_dir)
    cfg.ensure_dirs()
    runbook = Pilot3SoakRunbookBuilder(base_dir=args.output_dir).write(cfg)

    design = Pilot3ComparativeDesign()
    comparison_design = {
        "arms": list(Pilot3ComparisonArm.ALL),
        "central_question": "Does simulated action/reaction produce stronger "
                            "grounding than perception-only exposure?",
        "metrics_compared": design.to_dict()["metrics_compared"],
        "real_world_action_evidence": 0,
    }
    governance_checklist = [
        "enable_pilot3_soak (granted by default)",
        "enable_pilot3_firewall_preflight (granted by default)",
        "enable_pilot3_dry_run_trace (granted by default)",
        "enable_pilot3_gridworld_short (allowed if firewall preflight passes)",
        "enable_pilot3_gridworld_soak_simulated (bounded config + approval)",
        "enable_pilot3_mixed_sensory_gridworld (needs sensory validation)",
        "enable_pilot3_post_analysis (read-only; granted by default)",
    ]
    cfg_path = os.path.join(args.output_dir, "pilot3_config.json")
    with open(cfg_path, "w", encoding="utf-8") as fh:
        json.dump(cfg.to_dict(), fh, indent=2, default=str)
    design_path = os.path.join(args.output_dir, "comparison_design.json")
    with open(design_path, "w", encoding="utf-8") as fh:
        json.dump(comparison_design, fh, indent=2, default=str)
    gov_path = os.path.join(args.output_dir, "governance_checklist.json")
    with open(gov_path, "w", encoding="utf-8") as fh:
        json.dump(governance_checklist, fh, indent=2, default=str)

    print("=== Pilot-3 soak plan (plan only; no run started) ===")
    print(f"pilot id    : {cfg.pilot3_id}")
    print(f"mode        : {cfg.mode} ({cfg.time_label})")
    print(f"real_world_authority : {cfg.real_world_authority}")
    print(f"runbook     : {runbook}")
    print(f"config      : {cfg_path}")
    print(f"comparison  : {design_path}")
    print(f"governance  : {gov_path}")
    print("note        : Pilot-3 is simulation-only sandboxed action "
          "grounding; the system never acts on the real world")


if __name__ == "__main__":
    main()
