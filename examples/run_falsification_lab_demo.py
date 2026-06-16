#!/usr/bin/env python3
"""Falsification lab demo: shuffled order, random labels, passive parser.

    python examples/run_falsification_lab_demo.py --state-dir .solaris_ai_nn_replication/test_falsification

Runs bounded falsification tests against a developmental claim: does shuffled
time destroy prediction? do concepts form from features rather than labels? does
a passive parser reproduce the same structure? Findings are conservative;
passing a test does not prove understanding; original evidence is never modified.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.developmental_replication import (
    FalsificationTest,
    FalsificationTestType,
)


def main():
    parser = argparse.ArgumentParser(description="Falsification lab demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_replication/test_falsification")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    run_profile = {
        "durable_prediction_improvement_score": 0.8,
        "concept_family_distribution": {"rf": 3, "vib": 2},
        "sign_family_distribution": {"s1": 2, "s2": 1},
    }
    lab = FalsificationTest()

    # Shuffled time SHOULD collapse prediction (claim survives = passed).
    shuffled = lab.run(FalsificationTestType.SHUFFLED_EVENT_ORDER,
                       run_profile=run_profile,
                       null_profile={"durable_prediction_improvement_score": 0.1})
    # Random labels but same features SHOULD keep concepts (passed).
    random_labels = lab.run(
        FalsificationTestType.RANDOM_LABELS_SAME_FEATURES,
        run_profile=run_profile,
        null_profile={"concept_family_distribution": {"rf": 3, "vib": 2}})
    # Passive parser reproduces the SAME families -> the stack added nothing
    # (falsified).
    passive = lab.run(
        FalsificationTestType.PASSIVE_PARSER_COMPARISON,
        run_profile=run_profile,
        null_profile={"sign_family_distribution": {"s1": 2, "s2": 1}})

    print("=== Falsification lab demo ===")
    for name, result in (("shuffled_event_order", shuffled),
                         ("random_labels_same_features", random_labels),
                         ("passive_parser_comparison", passive)):
        print(f"  {name:30s} -> {result.outcome}")
        print(f"      Q: {result.question}")
        for f in result.findings:
            print(f"      - {f.statement}")
    print(f"original evidence modified: {passive.original_modified}")
    print("note: passing a falsification test does not prove understanding; a "
          "failed claim is made visible; not consciousness or life.")


if __name__ == "__main__":
    main()
