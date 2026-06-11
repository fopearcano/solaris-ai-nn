#!/usr/bin/env python3
"""Executive demo: arbitration between Desire and Action, signal-only.

    python examples/run_executive_demo.py --steps 200

Homeostasis produces Desire candidates; the executive queues them, inhibits
the unsafe/over-budget, runs bounded prospection, scores everything with the
penalties dominating, and emits one suggestion per arbitration -- recorded
in the decision trace. No real action anywhere.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.executive import (
    ExecutiveQueryInterface,
    ExecutiveReportBuilder,
)
from solaris_ai_nn.runtime.continuous_runner import ContinuousRunner
from solaris_ai_nn.signals import canonical as C


def main() -> None:
    parser = argparse.ArgumentParser(description="Executive demo")
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/executive_demo")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    active = (2 * args.steps) // 3

    def provider(step):
        if step <= active:
            return C.Stimulus(payload=["light", "noise"][step % 2],
                              intensity=0.5)
        return None

    def reaction(result, stim):
        return 1.0 if result["suggested_action"] == "look" else -0.4

    runner = ContinuousRunner(
        state_dir=args.state_dir, max_steps=args.steps, seed=args.seed,
        action_labels=["look", "rest", "explore_safely", "stabilize"],
        vocabulary=["light", "noise"],
        stimulus_provider=provider, reaction_provider=reaction,
        enable_homeostasis=True, enable_executive=True,
        executive_report_interval_steps=max(25, args.steps // 4))
    runner.run()
    layer = runner.executive
    summary = layer.summary()

    print("=" * 70)
    print("Solaris-AI-NN -- executive demo (arbitration, not agency)")
    print("=" * 70)
    print(f"mode:                {summary['mode']}")
    print(f"arbitrations:        {summary['decisions']}")
    print(f"selected suggestion: {summary['selected_action_suggestion']}")
    print(f"active focus:        {summary['active_focus']}")
    print(f"inhibitions:         {summary['inhibited_candidate_count']}")
    print(f"no-safe-action:      {summary['no_safe_action_count']}")
    print()
    result = layer.last_result
    print("last arbitration score table:")
    for score in result.scores[:6]:
        mark = "BLOCKED" if score.blocked else "ok     "
        print(f"  [{mark}] {score.candidate.label:24s} "
              f"total={score.total:7.2f}")
    print()
    queries = ExecutiveQueryInterface(layer)
    for question in ("why was this action selected?",
                     "what candidates were rejected?",
                     "what score won arbitration?"):
        print(f"Q: {question}")
        print(f"A: {queries.answer(question).text[:170]}")
        print()
    paths = ExecutiveReportBuilder(layer).save(
        Path(args.state_dir) / "executive_report.json",
        Path(args.state_dir) / "executive_report.md")
    print(f"report:         {paths['markdown']} "
          f"(claim guard safe: {paths['claim_guard']['safe']})")
    print(f"decision trace: {args.state_dir}/decision_trace.jsonl")


if __name__ == "__main__":
    main()
