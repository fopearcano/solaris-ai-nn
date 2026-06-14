#!/usr/bin/env python3
"""Accumulation-vs-growth demo: accumulation, weak-growth, and regression cases.

    python examples/run_accumulation_vs_growth_demo.py --state-dir .solaris_ai_nn_pilot1/test_growth_discrimination

Runs the discriminator on three hand-built mock comparisons and prints the
conservative classification for each. 'Growth' here means durable operational
structural change, never consciousness.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.post_pilot import (
    AccumulationVsGrowthAnalyzer,
    BaselineComparator,
)


class _FakeArtifacts:
    """Stand-in with the core artifacts present so results aren't inconclusive."""

    class _Idx:
        present = ["developmental_state", "proto_symbols", "hypotheses",
                   "observability"]

    index = _Idx()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Accumulation vs growth demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_pilot1/test_growth_discrimination")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    comparator = BaselineComparator()
    analyzer = AccumulationVsGrowthAnalyzer()
    arts = _FakeArtifacts()

    cases = {
        "accumulation_only": comparator.compare_dicts(
            "b", {"proto_symbol_count": 2, "hypothesis_count": 1,
                  "compression_ratio": 1.0},
            "a", {"proto_symbol_count": 80, "hypothesis_count": 60,
                  "compression_ratio": 1.0}),
        "weak_growth": comparator.compare_dicts(
            "b", {"compression_ratio": 1.0, "prediction_score": 0.5},
            "a", {"compression_ratio": 1.2, "prediction_score": 0.5}),
        "regression": comparator.compare_dicts(
            "b", {"prediction_score": 0.7, "compression_ratio": 1.5,
                  "ambiguous_symbol_ratio": 0.2},
            "a", {"prediction_score": 0.3, "compression_ratio": 1.0,
                  "ambiguous_symbol_ratio": 0.6}),
    }

    print("=== Accumulation vs growth ===")
    results = {}
    for name, cmp in cases.items():
        result = analyzer.analyze(cmp, [], arts)
        results[name] = result.to_dict()
        print(f"  {name:<18} -> {result.final_classification} "
              f"(acc={result.accumulation_score}, grow={result.growth_score})")
    out = os.path.join(args.state_dir, "growth_discrimination.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, default=str)
    print(f"written: {out}")


if __name__ == "__main__":
    main()
