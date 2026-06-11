#!/usr/bin/env python3
"""World model prediction demo: graph counts vs a changing world.

    python examples/run_world_model_prediction_demo.py --steps 200

Phase 1 feeds a predictable stream and scores graph-based predictions
against it (they should mostly hit). Phase 2 changes the pattern: the same
graph now misses, and Mysterium (unknown pressure) rises accordingly.
Predictions are based on graph counts and never execute anything.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.latent import MysteriumTracker
from solaris_ai_nn.world_model import WorldModelBuilder


class _Stim:
    def __init__(self, kind, payload, is_absence=False):
        self.kind = kind
        self.payload = payload
        self.is_absence = is_absence
        self.intensity = 0.5


def main() -> None:
    parser = argparse.ArgumentParser(
        description="World model prediction demo")
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/world_prediction")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    mysterium = MysteriumTracker()
    builder = WorldModelBuilder(mysterium=mysterium)
    half = args.steps // 2

    # Phase 1: a strictly repeating world the graph can count.
    for i in range(half):
        stim = _Stim("Stimulus", ["light", "noise"][i % 2])
        builder.update_from_signal(stim, {
            "input_type": "Stimulus", "pattern_key": stim.payload,
            "suggested_action": "approach", "is_absence": False})
        builder.update_from_reaction("approach", 1.0)
    phase1_hits = 0
    for _ in range(10):
        prediction = builder.predictor.predict_next(
            {"context": "awake", "action": "approach"}, builder.graph)
        score = builder.predictor.score_prediction(prediction, {
            "signal_type": "Stimulus", "valence_bucket": "positive",
            "is_absence": False})
        phase1_hits += int(score["hit"])
    pressure_after_phase1 = mysterium.pressure

    # Phase 2: the world changes; the same graph counts now mislead.
    for i in range(half):
        stim = _Stim("Reaction" if i % 2 else "Push", f"odd{i % 5}",
                     is_absence=(i % 3 == 0))
        builder.update_from_signal(stim, {
            "input_type": stim.kind, "pattern_key": stim.payload,
            "suggested_action": "withdraw", "is_absence": stim.is_absence})
        builder.update_from_reaction("withdraw", -0.8)
    phase2_hits = 0
    for _ in range(10):
        prediction = builder.predictor.predict_next(
            {"context": "awake", "action": "approach"}, builder.graph)
        score = builder.predictor.score_prediction(prediction, {
            "signal_type": "MeaningEvent", "valence_bucket": "negative",
            "is_absence": True})
        phase2_hits += int(score["hit"])

    print("=" * 70)
    print("Solaris-AI-NN -- world model prediction demo")
    print("=" * 70)
    print(f"phase 1 (predictable): {phase1_hits}/10 graph predictions hit")
    print(f"  unknown pressure:    {pressure_after_phase1:.3f}")
    print(f"phase 2 (changed):     {phase2_hits}/10 graph predictions hit")
    print(f"  unknown pressure:    {mysterium.pressure:.3f} "
          f"({mysterium.level()}, trend {mysterium.trend()})")
    print(f"overall accuracy:      {builder.predictor.accuracy()}")
    print()
    print("recent unknown-pressure reasons:")
    for row in mysterium.reasons[-4:]:
        sign = "+" if row["delta"] > 0 else "-"
        print(f"  {sign}{abs(row['delta']):.2f}  {row['reason']}")
    print()
    print("note: predictions are based on graph counts; they inform "
          "trackers and never execute actions.")


if __name__ == "__main__":
    main()
