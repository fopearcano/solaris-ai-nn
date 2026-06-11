#!/usr/bin/env python3
"""Homeostasis demo: a bounded signal-only run with the need economy on.

    python examples/run_homeostasis_demo.py --steps 200

Input flows, then goes quiet: variables move, needs rise, drives aggregate,
valence tracks the feedback, and Desire candidates bias the bridge's
suggestions. No real action, no authority -- pressure numbers with receipts.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.homeostasis import (
    HomeostasisQueryInterface,
    HomeostasisReportBuilder,
)
from solaris_ai_nn.runtime.continuous_runner import ContinuousRunner
from solaris_ai_nn.signals import canonical as C


def main() -> None:
    parser = argparse.ArgumentParser(description="Homeostasis demo")
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/homeostasis_demo")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    active = (2 * args.steps) // 3

    def provider(step):
        if step <= active:
            return C.Stimulus(payload=["light", "noise"][step % 2],
                              intensity=0.5)
        return None  # silence raises seek_signal / low-stimulus pressure

    def reaction(result, stim):
        return 1.0 if result["suggested_action"] == "look" else -0.4

    runner = ContinuousRunner(
        state_dir=args.state_dir, max_steps=args.steps, seed=args.seed,
        action_labels=["look", "rest", "explore_safely", "stabilize"],
        vocabulary=["light", "noise"],
        stimulus_provider=provider, reaction_provider=reaction,
        enable_homeostasis=True, homeostasis_update_interval_steps=10)
    runner.run()
    regulator = runner.homeostasis
    summary = regulator.summary()

    print("=" * 70)
    print("Solaris-AI-NN -- homeostasis demo (pressure, not will)")
    print("=" * 70)
    print(f"regulation updates:  {summary['updates']}")
    print(f"dominant need:       {summary['dominant_need']}")
    print(f"dominant drive:      {summary['dominant_drive']}")
    print(f"valence (rolling):   {regulator.valence.rolling()} "
          f"({summary['valence_trend']})")
    print(f"being/not-being:     {summary['being_pressure']} / "
          f"{summary['not_being_pressure']} -> "
          f"{summary['action_implication']}")
    print(f"best desire:         {summary['best_desire']} (a suggestion, "
          "never an act)")
    print(f"suppressed desires:  {summary['suppressed_desire_count']}")
    print()
    queries = HomeostasisQueryInterface(regulator)
    for question in ("what is the dominant need?",
                     "why was this desire suggested?",
                     "what drive is strongest?"):
        print(f"Q: {question}")
        print(f"A: {queries.answer(question).text[:170]}")
        print()
    paths = HomeostasisReportBuilder(regulator).save(
        Path(args.state_dir) / "homeostasis_report.json",
        Path(args.state_dir) / "homeostasis_report.md")
    print(f"report: {paths['markdown']} "
          f"(claim guard safe: {paths['claim_guard']['safe']})")
    print(f"need trace: {args.state_dir}/need_trace.jsonl")


if __name__ == "__main__":
    main()
