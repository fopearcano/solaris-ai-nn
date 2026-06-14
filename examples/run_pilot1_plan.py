#!/usr/bin/env python3
"""Pilot-1 plan-only demo: write the runbook, budget, and config -- start nothing.

    python examples/run_pilot1_plan.py --output-dir .solaris_ai_nn_pilot1/test_plan

Generates the operator runbook, a resource-budget estimate, and a pilot config
template for a month-scale Pilot-1 window. It is plan-only: it never starts a
real run, never confuses simulated time with real time, and treats no output
as proof of consciousness.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.pilot1 import (
    OperatorRunbookBuilder,
    PilotConfig,
    PilotMode,
    ResourceBudgetMonitor,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pilot-1 plan only")
    parser.add_argument("--output-dir", type=str,
                        default=".solaris_ai_nn_pilot1/test_plan")
    args = parser.parse_args()

    cfg = PilotConfig(mode=PilotMode.PLAN_ONLY, base_dir=args.output_dir)
    cfg.environment().ensure()

    runbook_path = OperatorRunbookBuilder(base_dir=args.output_dir).write(cfg)
    env = cfg.environment()
    budget = ResourceBudgetMonitor(
        state_dir=env.state_dir, artifact_dir=env.artifact_dir,
        log_dir=env.log_dir, report_dir=env.report_dir).estimate()
    cfg_path = os.path.join(args.output_dir, "pilot_config.json")
    with open(cfg_path, "w", encoding="utf-8") as fh:
        json.dump(cfg.to_dict(), fh, indent=2, default=str)

    print("=== Pilot-1 plan (plan only; no run started) ===")
    print(f"pilot id     : {cfg.pilot_id}")
    print(f"mode         : {cfg.mode} ({cfg.time_label})")
    print(f"runbook      : {runbook_path}")
    print(f"config       : {cfg_path}")
    print(f"proj 30d disk: {budget.projected_30d_mb} MB "
          f"(budget {cfg.max_disk_mb} MB)")
    print("note         : plan only; a real soak needs governance approval, "
          "preflight, and an operator decision")


if __name__ == "__main__":
    main()
