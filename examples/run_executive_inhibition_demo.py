#!/usr/bin/env python3
"""Executive inhibition demo: every rule family, one contradictory moment.

    python examples/run_executive_inhibition_demo.py

High curiosity meets an unsafe action candidate, a governance boundary, low
energy, and a latent context -- and the inhibition table shows exactly which
family suppressed what, and why. Nothing is dropped silently.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.executive import ExecutiveLayer, ExecutiveQueryInterface
from solaris_ai_nn.homeostasis import HomeostaticRegulator


def main() -> None:
    parser = argparse.ArgumentParser(description="Executive inhibition demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/exec_inhibition")
    args = parser.parse_args()

    # High curiosity + low energy desires from the homeostasis layer.
    regulator = HomeostaticRegulator()
    desires = regulator.update({
        "latent": {"mysterium_pressure": 0.9,
                   "anticipation_accuracy": 0.3},
        "embodiment": {"energy": 0.8, "max_energy": 10.0,
                       "exhausted": True},
    }).desire_candidates

    layer = ExecutiveLayer(state_dir=args.state_dir)
    decision = layer.decide(
        desires,
        context={
            "energy": 0.08,                       # resource inhibition
            "governance_blocks": {"run_replay":   # governance inhibition
                                  "operator paused replay output"},
            "latent_budget_exceeded": False,
        },
        readout_suggestion="motor_forward",       # safety inhibition
        step=1)

    print("=" * 70)
    print("Solaris-AI-NN -- executive inhibition demo")
    print("=" * 70)
    print("the moment: high curiosity, exhausted body, a real-world-shaped")
    print("readout suggestion, and a governance block on replay output")
    print()
    print("inhibition table:")
    for row in layer.inhibition.history:
        print(f"  [{row['family']:10s}] {row['label']:24s} "
              f"{row['reason'][:58]}")
    for score in layer.last_result.scores:
        if score.candidate.inhibited \
                and score.candidate.inhibition_reason:
            print(f"  [{'candidate':10s}] {score.candidate.label:24s} "
                  f"{score.candidate.inhibition_reason[:58]}")
    print()
    print(f"selected: {decision.selected.label!r} "
          f"(fallback: {decision.fallback_used})")
    print(f"reason:   {decision.reason[:90]}")
    print()
    queries = ExecutiveQueryInterface(layer)
    print("Q: what was inhibited?")
    print(f"A: {queries.answer('what was inhibited?').text[:200]}")
    print()
    print("note: inhibition is explainable suppression; every blocked "
          "candidate stays on the record.")


if __name__ == "__main__":
    main()
