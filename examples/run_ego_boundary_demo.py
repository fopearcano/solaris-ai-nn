#!/usr/bin/env python3
"""Ego boundary demo: the operational self-model in a bounded run.

    python examples/run_ego_boundary_demo.py --steps 150

A bounded continuous run with the ego layer enabled: identity anchors are
captured, the sixteen boundaries are registered and checked, events are
classified internal/external/simulated, and the run ends with the boundary
registry and a ClaimGuard-scanned self-report. No real actions anywhere --
and no consciousness claim, because there is nothing to claim.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.ego import SelfReportBuilder
from solaris_ai_nn.runtime.continuous_runner import ContinuousRunner
from solaris_ai_nn.signals import canonical as C


def main() -> None:
    parser = argparse.ArgumentParser(description="Ego boundary demo")
    parser.add_argument("--steps", type=int, default=150)
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/ego_boundary_demo")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    active = (2 * args.steps) // 3

    def provider(step):
        if step <= active:
            return C.Stimulus(payload=["light", "noise"][step % 2],
                              intensity=0.5)
        return None

    runner = ContinuousRunner(
        state_dir=args.state_dir, max_steps=args.steps, seed=args.seed,
        stimulus_provider=provider,
        enable_homeostasis=True, enable_executive=True, enable_ego=True,
        ego_update_interval_steps=max(10, args.steps // 5))
    runner.run()

    ego = runner.ego
    # Classify a few representative events through the self-model.
    for event in ({"source": "homeostasis", "kind": "desire_candidate",
                   "label": "rest"},
                  {"source": "stream", "kind": "stream_line",
                   "payload": "external text"},
                  {"source": "counterfactual", "kind": "dream_trace"}):
        ego.classify_event(event)

    summary = ego.summary()
    print("=" * 70)
    print("Solaris-AI-NN -- ego boundary demo (operational, not "
          "metaphysical)")
    print("=" * 70)
    print(f"steps:                {runner.telemetry.lifetime_steps}")
    print(f"perspective:          {summary['perspective']}")
    print(f"identity continuity:  {summary['identity_continuity']:.2f}")
    print(f"action authority:     {summary['action_authority']}")
    print(f"classifications:      {summary['classification_counts']}")
    print(f"boundary violations:  {summary['boundary_violation_count']}")
    print()
    print(ego.boundaries.to_markdown())
    builder = SelfReportBuilder(ego)
    paths = builder.save(Path(args.state_dir) / "self_report.json",
                         Path(args.state_dir) / "self_report.md")
    print(f"self-report:    {paths['markdown']} "
          f"(claim guard safe: {paths['claim_guard']['safe']})")
    print(f"narrative:      {summary['narrative_trace_path']}")
    print()
    print("note: the self-model observes and classifies; it executes "
          "nothing, grants nothing, and claims no consciousness.")


if __name__ == "__main__":
    main()
