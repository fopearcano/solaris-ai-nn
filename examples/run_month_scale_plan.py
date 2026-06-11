#!/usr/bin/env python3
"""Month-scale plan generator: a plan, a budget, a checklist -- no run.

    python examples/run_month_scale_plan.py

Generates the month-scale testing plan (segments, checkpoints,
consolidation windows, report cadence), estimates the state/artifact
budget, and prints the governance checklist that must be satisfied before
any real month-scale run starts. Nothing long-running is launched.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.developmental import DevelopmentalRuntime
from solaris_ai_nn.governance.policy import GovernancePolicy


def main() -> None:
    parser = argparse.ArgumentParser(description="Month-scale plan")
    parser.add_argument("--output-dir", type=str,
                        default=".solaris_ai_nn_ops/month_plan")
    parser.add_argument("--target-days", type=int, default=30)
    args = parser.parse_args()

    days = args.target_days
    plan = {
        "mode": "month_scale_developmental",
        "target_runtime_days": days,
        "time": "real wall-clock (simulated_time=False)",
        "segments": {
            "segment_length_steps": 5000,
            "checkpoint_interval_steps": 250,
            "consolidation_interval_steps": 1000,
            "epoch_check_interval_steps": 1000,
            "long_report_interval": "daily",
        },
        "budget_estimate": {
            "checkpoints_per_day": 24,
            "state_dir_mb_per_week": 50,
            "artifact_dir_mb_per_week": 30,
            "fossil_memory_rows_per_month": "tens, not thousands",
            "transcript_and_audit_mb_per_month": 20,
            "total_disk_budget_mb": days * 12,
        },
        "maintenance": [
            "daily: consolidation + growth/drift snapshot",
            "weekly: developmental report + pruning dry-run review",
            "monthly: fossil memory review + epoch history audit",
        ],
        "stop_conditions": [
            "watchdog/emergency stop (always available)",
            "memory layer over budget for two consecutive checks",
            "uncontrolled drift warning sustained for one day",
            "identity continuity degrading across restarts",
        ],
    }
    checklist = [
        ("enable_developmental_runtime scope granted",
         GovernancePolicy().permissions.allows(
             "enable_developmental_runtime")),
        ("enable_month_scale_testing approval recorded", False),
        ("bounded run manifest with checkpoint intervals", False),
        ("watchdog + safe shutdown wired and tested", False),
        ("disk budget reserved and rotation configured", False),
        ("operator review cadence agreed (weekly)", False),
    ]

    print("=" * 70)
    print("Solaris-AI-NN -- month-scale run PLAN (no run is started)")
    print("=" * 70)
    print(json.dumps(plan, indent=2))
    print()
    print("governance checklist (all must hold before launch):")
    for item, satisfied in checklist:
        print(f"  [{'x' if satisfied else ' '}] {item}")
    print()
    # Prove the gate: a month-scale runtime without approval is refused.
    try:
        DevelopmentalRuntime(state_dir=args.output_dir + "/refused",
                             enable_month_scale=True,
                             max_steps=10).run()
        gate = "FAILED (this should not happen)"
    except PermissionError as exc:
        gate = f"refused as designed ({str(exc)[:60]}...)"
    print(f"month-scale gate check: {gate}")

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "month_scale_plan.json", "w", encoding="utf-8") as fh:
        json.dump({"plan": plan,
                   "checklist": [{"item": i, "satisfied": s}
                                 for i, s in checklist]}, fh, indent=2)
    print(f"plan saved: {out / 'month_scale_plan.json'}")
    print()
    print("note: this script generates a plan only; month-scale testing "
          "requires explicit governance approval and starts nothing by "
          "itself.")


if __name__ == "__main__":
    main()
