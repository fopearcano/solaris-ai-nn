#!/usr/bin/env python3
"""Pilot-2 read-only plan: source/governance checklist + budget; no long run.

    python examples/run_pilot2_read_only_plan.py --output-dir .solaris_ai_nn_pilot2/test_plan

Generates a Pilot-2 read-only sensory plan: a source checklist, a governance
checklist, and a resource-budget estimate. It starts no long run, grants no
real-world authority, and begins Pilot-2 with read-only grounding rather than
autonomy.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.pilot1 import ResourceBudgetMonitor
from solaris_ai_nn.sensory_membrane import SensorySourceType


def main():
    parser = argparse.ArgumentParser(description="Pilot-2 read-only plan")
    parser.add_argument("--output-dir", type=str,
                        default=".solaris_ai_nn_pilot2/test_plan")
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    budget = ResourceBudgetMonitor(state_dir=args.output_dir).estimate()
    plan = {
        "pilot": "pilot2_read_only",
        "purpose": "Test whether Solaris-AI-NN develops differently under a "
                   "less artificial, read-only environmental exposure.",
        "principle": "The world may enter the system; the system may not act "
                     "on the world.",
        "source_checklist": [
            {"type": t, "read_only": True,
             "simulated": t in SensorySourceType.SIMULATED}
            for t in (SensorySourceType.JSONL_FILE,
                      SensorySourceType.TEXT_FILE,
                      SensorySourceType.NUMERIC_CSV,
                      SensorySourceType.FOLDER_POLL,
                      SensorySourceType.SIMULATED_CAMERA_METADATA,
                      SensorySourceType.SIMULATED_AUDIO_METADATA)],
        "governance_checklist": [
            "enable_sensory_membrane (granted by default)",
            "enable_sensory_membrane_dry_run (granted by default)",
            "enable_real_read_only_sources (requires approval)",
            "enable_folder_poll_source (requires allowed root + approval)",
            "enable_pilot2_read_only_short (requires approval)",
            "enable_pilot2_real_read_only_soak (requires approval)",
        ],
        "resource_budget": budget.to_dict(),
        "hard_boundaries": [
            "no writes to sources", "no deletion/rename", "no command "
            "execution", "no network calls", "no device capture",
            "input text is never an operator command",
            "no real-world actuation",
        ],
        "starts_long_run": False,
    }
    path = os.path.join(args.output_dir, "PILOT2_READ_ONLY_PLAN.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(plan, fh, indent=2, default=str)

    print("=== Pilot-2 read-only plan (plan only; no run started) ===")
    print(f"sources in checklist : {len(plan['source_checklist'])}")
    print(f"governance items     : {len(plan['governance_checklist'])}")
    print(f"projected 30d disk   : {budget.projected_30d_mb} MB")
    print(f"plan                 : {path}")
    print("note                 : read-only grounding, not autonomy; the "
          "system never acts on the world")


if __name__ == "__main__":
    main()
