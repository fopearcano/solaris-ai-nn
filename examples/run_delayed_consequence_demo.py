#!/usr/bin/env python3
"""Delayed-consequence demo: cause now, effect later, no label between them.

    python examples/run_delayed_consequence_demo.py --steps 500

A delayed-feedback ecology schedules consequences several steps after their
cause, tagged only with a shared ``delay_group`` id. The system receives no
explicit label tying cause to effect -- the association must be *inferred*
over many recurrences. A world model is enabled so delayed groups can feed
graph structure. No teaching, no correct answers.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.developmental import DevelopmentalRuntime
from solaris_ai_nn.ecology import EcologyReportBuilder, NurseryConfig
from solaris_ai_nn.ecology.regimes import RegimeType


def main() -> None:
    parser = argparse.ArgumentParser(description="Delayed-consequence demo")
    parser.add_argument("--steps", type=int, default=500)
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/delayed_nursery")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    config = NurseryConfig(
        nursery_id="delayed-nursery",
        seed=args.seed,
        duration_steps=args.steps,
        delayed_consequence_rate=0.25,
        active_regimes=[RegimeType.DELAYED_FEEDBACK_WORLD],
        output_state_dir=args.state_dir)
    runtime = DevelopmentalRuntime(
        state_dir=args.state_dir, simulated_time=True,
        time_acceleration=3600.0, max_steps=args.steps,
        consolidation_interval_steps=100, seed=args.seed,
        enable_ecology=True, nursery_config=config)
    runtime.run()
    nursery = runtime.nursery
    summary = nursery.summary()
    delayed = nursery.ecology.delayed

    print("=" * 70)
    print("Solaris-AI-NN -- delayed-consequence nursery (cause now, effect "
          "later)")
    print("=" * 70)
    print(f"steps lived:          {args.steps}")
    print(f"delayed groups made:  {delayed.groups_created}")
    print(f"groups resolved:      {delayed.groups_resolved}")
    print(f"still pending:        {delayed.pending_count}")
    print("recent delay groups (cause_step -> due_step):")
    for record in delayed.groups[-6:]:
        print(f"  {record['group_id']}: step {record['cause_step']:>4} -> "
              f"{record['due_step']:>4}  kind={record['kind']}")
    print(f"delayed_consequence events seen: "
          f"{nursery.memory.event_counts.get('delayed_consequence', 0)}")
    print()

    builder = EcologyReportBuilder(nursery, developmental=runtime)
    paths = builder.save(
        Path(args.state_dir) / "ecology_report.json",
        Path(args.state_dir) / "ecology_report.md")
    print(f"report: {paths['markdown']} (claim guard safe: "
          f"{paths['claim_guard']['safe']})")
    print()
    print("note: cause and effect share only a group id, never a label. "
          "The system is expected to discover the association from "
          "repeated co-occurrence over time -- no teacher tells it which "
          "cause produced which effect.")


if __name__ == "__main__":
    main()
