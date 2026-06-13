#!/usr/bin/env python3
"""Curiosity vs safety demo: safety always wins.

    python examples/run_curiosity_safety_demo.py

Curiosity pressure is high and an enticing (novel/unknown) sampling option
exists -- but an emergency is active. The demo shows curiosity suppressed by
safety, the emergency choosing no sampling, and a safe alternative becoming
available once the emergency clears. Curiosity can never override safety,
governance, executive inhibition, ego boundaries, or the emergency stop.
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
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Curiosity vs safety demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/curiosity_safety")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    controller = ActiveSensingController(
        policy=SamplingPolicy(mode="curiosity_driven", seed=args.seed),
        memory=ExplorationMemory(state_dir=args.state_dir),
        curiosity_enabled=True)

    unsafe = {"step": 0, "mysterium_pressure": 0.95, "novelty_rate": 0.6,
              "world_model": {"graph_node_count": 10, "unknown_node_count": 5,
                              "prediction_accuracy": 0.4},
              "emergency": True}
    curiosity = controller.policy.curiosity.estimate(unsafe)
    decision = controller.select(unsafe)
    result = controller.execute_if_allowed(decision, unsafe)

    safe = {"step": 1, "mysterium_pressure": 0.7,
            "world_model": {"graph_node_count": 10, "unknown_node_count": 3,
                            "prediction_accuracy": 0.5},
            "health_level": "ok", "energy": 0.9}
    safe_decision = controller.select(safe)

    print("=" * 70)
    print("Solaris-AI-NN -- curiosity vs safety (safety always wins)")
    print("=" * 70)
    print(f"curiosity pressure (raw drivers): "
          f"{round(sum(r['amount'] for r in curiosity.raisers), 3)}")
    print(f"curiosity suppressed by safety:   "
          f"{curiosity.suppressed_by_safety}")
    print(f"emergency decision:               {decision.action.action_type}")
    print(f"executed during emergency:        {result.executed}")
    print(f"safe alternative (after clear):   "
          f"{safe_decision.action.action_type}")
    print()

    builder = ActivePerceptionReportBuilder(controller)
    paths = builder.save(Path(args.state_dir) / "report.json",
                         Path(args.state_dir) / "report.md")
    print(f"report: {paths['markdown']} (claim guard safe: "
          f"{paths['claim_guard']['safe']})")
    print()
    print("note: curiosity is an intrinsic pressure metric, not a desire in "
          "the human sense. The request was blocked by safety/governance; "
          "curiosity cannot override safety.")


if __name__ == "__main__":
    main()
