#!/usr/bin/env python3
"""Uncertainty sampling demo: target the weakest part of the world model.

    python examples/run_uncertainty_sampling_demo.py

An ambiguous, low-confidence world-model region drives uncertainty up. The
sampling policy selects an action that targets it; we show prediction and
uncertainty before and after. The "after" improvement here is illustrative
(a simulated measured reduction), and information gain is a hedged heuristic.
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
    parser = argparse.ArgumentParser(description="Uncertainty sampling demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/uncertainty_sampling")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    controller = ActiveSensingController(
        policy=SamplingPolicy(mode="balanced", seed=args.seed),
        memory=ExplorationMemory(state_dir=args.state_dir))
    before = {
        "step": 0, "mysterium_pressure": 0.7,
        "world_model": {"graph_node_count": 12, "unknown_node_count": 6,
                        "prediction_accuracy": 0.40,
                        "low_confidence_nodes": ["node_unknown_3"]},
        "health_level": "ok", "energy": 0.9,
    }
    decision = controller.select(before)
    result = controller.execute_if_allowed(decision, before)
    after = {
        "step": 1, "mysterium_pressure": 0.55,
        "world_model": {"graph_node_count": 12, "unknown_node_count": 4,
                        "prediction_accuracy": 0.62},
    }
    record = controller.observe_result(result, before, after)

    print("=" * 70)
    print("Solaris-AI-NN -- uncertainty sampling (target the weakest region)")
    print("=" * 70)
    print(f"selected action:       {decision.action.action_type}")
    print(f"target_ref:            {decision.action.target_ref}")
    print(f"expected info gain:    {decision.action.expected_information_gain}")
    print(f"prediction before:     "
          f"{before['world_model']['prediction_accuracy']}")
    print(f"prediction after:      "
          f"{after['world_model']['prediction_accuracy']}")
    print(f"unknown nodes before:  {before['world_model']['unknown_node_count']}")
    print(f"unknown nodes after:   {after['world_model']['unknown_node_count']}")
    print(f"observed info gain:    {record.observed_information_gain}")
    print(f"outcome:               {record.outcome}")
    print()

    builder = ActivePerceptionReportBuilder(controller)
    paths = builder.save(Path(args.state_dir) / "report.json",
                         Path(args.state_dir) / "report.md")
    print(f"report: {paths['markdown']} (claim guard safe: "
          f"{paths['claim_guard']['safe']})")
    print()
    print("note: information gain is a low-compute heuristic with explicit "
          "confidence and uncertainty; the observed gain is a proxy measured "
          "after the fact, not proof of understanding.")


if __name__ == "__main__":
    main()
