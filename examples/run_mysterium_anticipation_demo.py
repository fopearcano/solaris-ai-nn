#!/usr/bin/env python3
"""Mysterium / anticipation demo: a predictable world, then a surprising one.

    python examples/run_mysterium_anticipation_demo.py --steps 200

Phase 1 feeds a strictly repeating pattern: anticipation accuracy climbs and
unknown pressure drains. Phase 2 scrambles the pattern: misses accumulate,
the miss streak grows, and Mysterium (the numeric unknown-pressure estimate)
rises -- with every change attributed to a named reason.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.latent import AnticipationTracker, MysteriumTracker


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mysterium / anticipation demo")
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/mysterium_demo")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    anticipation = AnticipationTracker()
    mysterium = MysteriumTracker()
    half = args.steps // 2

    def feed(event):
        score = anticipation.observe_actual(event)
        anticipation.predict({})
        if score is not None:
            accuracy = anticipation.rolling_accuracy()
            mysterium.update({
                "prediction_hit": score["hit"],
                "prediction_miss_streak": anticipation.miss_streak,
                "stable_patterns": score["hit"] and accuracy > 0.8,
                # Sustained unpredictability is itself unexplained error.
                "unexplained_error": 1.0 - accuracy,
            })

    # Phase 1: a strictly repeating, fully predictable pattern.
    anticipation.predict({})
    for i in range(half):
        feed({"input_type": "Stimulus", "suggested_action": "approach",
              "valence": 1.0, "is_absence": False, "reservoir_energy": 1.0})
    phase1_accuracy = anticipation.rolling_accuracy()
    phase1_pressure = mysterium.pressure

    # Phase 2: the pattern breaks -- kinds, actions, and valences scramble.
    import random
    rng = random.Random(args.seed)
    kinds = ["Stimulus", "Reaction", "Push", "MeaningEvent", "LogosTension"]
    actions = ["approach", "withdraw", "consume", "observe"]
    for i in range(args.steps - half):
        feed({"input_type": rng.choice(kinds),
              "suggested_action": rng.choice(actions),
              "valence": rng.uniform(-1, 1),
              "is_absence": rng.random() < 0.4,
              "reservoir_energy": rng.uniform(0, 10)})

    print("=" * 70)
    print("Solaris-AI-NN -- Mysterium / anticipation demo")
    print("=" * 70)
    print(f"phase 1 (predictable, {half} steps):")
    print(f"  rolling accuracy:  {phase1_accuracy:.3f}")
    print(f"  unknown pressure:  {phase1_pressure:.3f}")
    print(f"phase 2 (surprising, {args.steps - half} steps):")
    print(f"  rolling accuracy:  {anticipation.rolling_accuracy():.3f}")
    print(f"  unknown pressure:  {mysterium.pressure:.3f} "
          f"({mysterium.level()}, trend {mysterium.trend()})")
    print(f"  miss streak:       {anticipation.miss_streak}")
    print(f"  surprise estimate: {anticipation.surprise_estimate()}")
    print()
    print("recent unknown-pressure reasons:")
    for row in mysterium.reasons[-5:]:
        sign = "+" if row["delta"] > 0 else "-"
        print(f"  {sign}{abs(row['delta']):.2f}  {row['reason']} "
              f"(pressure -> {row['pressure']})")
    print()
    print("note: Mysterium is a numeric unknown-pressure estimate with "
          "attributed reasons; nothing mystical is measured.")


if __name__ == "__main__":
    main()
