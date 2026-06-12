#!/usr/bin/env python3
"""Symbol prediction demo: the semantic test, passed or failed honestly.

    python examples/run_symbol_prediction_demo.py

Markov-style next-symbol prediction over regular sequences beats the
frequency baseline; over shuffled noise it does not -- and both outcomes
are printed exactly as measured. Prediction is the cheapest honest test
of whether a symbol system carries structure.
"""

from __future__ import annotations

import argparse
import os
import random
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.protolanguage import SymbolPredictionEvaluator


def main() -> None:
    parser = argparse.ArgumentParser(description="Symbol prediction demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/symbol_prediction")
    args = parser.parse_args()
    del args  # nothing persists in this demo

    print("=" * 70)
    print("Solaris-AI-NN -- symbol prediction demo (honest either way)")
    print("=" * 70)

    # Case 1: structured sequences (a recurring loop).
    loop = ["ABS_0001", "NEED_SIGNAL_0001", "ACT_LOOK_0001",
            "RCT_NEUTRAL_0001"]
    structured = [loop for _ in range(10)]
    evaluator = SymbolPredictionEvaluator()
    evaluator.train_counts(structured[:7])
    comparison = evaluator.evaluate_holdout(structured[7:])
    print("structured sequences (recurring absence -> seek -> look "
          "loop):")
    print(f"  symbolic accuracy: {comparison['symbolic_accuracy']}")
    print(f"  baseline accuracy: {comparison['baseline_accuracy']}")
    print(f"  improvement:       "
          f"{comparison['improvement_over_baseline']:+} "
          f"({'improved' if comparison['improved'] else 'no improvement'})")
    print()

    # Case 2: shuffled noise (no structure to find).
    rng = random.Random(7)
    vocabulary = [f"SIG_N{i}_000{i}" for i in range(1, 6)]
    noise = [[rng.choice(vocabulary) for _ in range(4)]
             for _ in range(10)]
    noisy = SymbolPredictionEvaluator()
    noisy.train_counts(noise[:7])
    noise_comparison = noisy.evaluate_holdout(noise[7:])
    print("shuffled noise (no structure to find):")
    print(f"  symbolic accuracy: {noise_comparison['symbolic_accuracy']}")
    print(f"  baseline accuracy: {noise_comparison['baseline_accuracy']}")
    improvement = noise_comparison["improvement_over_baseline"]
    print(f"  improvement:       {improvement:+} "
          f"({'improved' if noise_comparison['improved'] else 'no improvement reported honestly'})")
    print()
    print("note: counts and Markov-style transitions only -- no ML. A "
          "symbol system that fails the prediction test is a finding, "
          "not an embarrassment to hide.")


if __name__ == "__main__":
    main()
