#!/usr/bin/env python3
"""Stagnation recovery demo: when the world goes flat, sample for novelty.

    python examples/run_stagnation_recovery_demo.py

A flat environment (no structural change, unresolved unknown pressure) trips
the stagnation detector. The policy then proposes safe novelty/unknown
sampling, and we report whether structural change improved afterward.
Stagnation is cautious: a calm stable phase is not the same as being stuck.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.active_perception import (
    ActivePerceptionReportBuilder,
    ActiveSensingController,
    ExplorationMemory,
    SamplingPolicy,
    StagnationDetector,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stagnation recovery demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/stagnation_recovery")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    detector = StagnationDetector()
    flat = {"structural_change_score": 0.0, "mysterium_pressure": 0.6,
            "developmental": {"structural_change_score": 0.0}}
    state = detector.detect(flat)

    controller = ActiveSensingController(
        policy=SamplingPolicy(mode="balanced", seed=args.seed),
        memory=ExplorationMemory(state_dir=args.state_dir))
    ctx = {"step": 0, "mysterium_pressure": 0.6,
           "structural_change_score": 0.0, "stagnation_status": state.status,
           "world_model": {"graph_node_count": 8, "unknown_node_count": 2,
                           "prediction_accuracy": 0.5},
           "health_level": "ok", "energy": 0.9}
    actions = controller.propose(ctx)
    action_types = [a.action_type for a in actions]
    decision = controller.select(ctx)
    result = controller.execute_if_allowed(decision, ctx)
    after = dict(ctx, step=1, structural_change_score=0.15)
    record = controller.observe_result(result, ctx, after)

    print("=" * 70)
    print("Solaris-AI-NN -- stagnation recovery (sample when the world is "
          "flat)")
    print("=" * 70)
    print(f"stagnation status:        {state.status}")
    print(f"recommended pressure:     {state.recommended_sampling_pressure}")
    print(f"indicators:               {state.indicators}")
    print(f"proposed sampling:        {action_types}")
    print(f"selected action:          {decision.action.action_type}")
    print(f"structural change before: {ctx['structural_change_score']}")
    print(f"structural change after:  {after['structural_change_score']}")
    print(f"sampling outcome:         {record.outcome}")
    print()

    builder = ActivePerceptionReportBuilder(controller)
    paths = builder.save(Path(args.state_dir) / "report.json",
                         Path(args.state_dir) / "report.md")
    print(f"report: {paths['markdown']} (claim guard safe: "
          f"{paths['claim_guard']['safe']})")
    print()
    print("note: stagnation is not always bad -- a stable phase with little "
          "change can be acceptable, and 'unknown' is reported when evidence "
          "is insufficient. Novelty-seeking is safe sampling, never autonomy.")


if __name__ == "__main__":
    main()
