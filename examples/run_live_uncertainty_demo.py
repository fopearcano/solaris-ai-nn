#!/usr/bin/env python3
"""Live uncertainty demo: low/high uncertainty; contradiction increases it.

    python examples/run_live_uncertainty_demo.py --state-dir .solaris_ai_nn_live/unc_demo

Estimates explicit uncertainty for three cases: a low-uncertainty trace (stable
multi-source sign with support), a high-uncertainty trace (thin single-source sign
with missing evidence), and a contradicted trace (counterevidence exceeds support).
Uncertainty is always explicit and high uncertainty prevents trace promotion.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.live_cognition import UncertaintyEstimator


def main():
    parser = argparse.ArgumentParser(description="Live uncertainty demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/unc_demo")
    args = parser.parse_args()

    est = UncertaintyEstimator()
    low = est.estimate(sign_stability=0.85, concept_stability=0.8,
                       source_reliability=0.9, source_count=2, modality_count=2,
                       recurrence=6, rhythm_present=True, supporting_count=6,
                       counter_count=0)
    high = est.estimate(sign_stability=0.2, concept_stability=0.2,
                        source_reliability=0.5, source_count=1, modality_count=1,
                        recurrence=1, supporting_count=0, missing_evidence=True)
    contradicted = est.estimate(sign_stability=0.7, concept_stability=0.7,
                                source_reliability=0.8, source_count=2,
                                modality_count=2, recurrence=5,
                                supporting_count=3, counter_count=6)

    print("=== Live uncertainty demo ===")
    print(f"  low-uncertainty trace   : {low.uncertainty:.2f} "
          f"(low={low.low})")
    print(f"  high-uncertainty trace  : {high.uncertainty:.2f} "
          f"(low={high.low}); notes: {high.notes}")
    print(f"  contradicted trace      : {contradicted.uncertainty:.2f} "
          f"(low={contradicted.low}); notes: {contradicted.notes}")
    print(f"  contradiction raises it : "
          f"{contradicted.uncertainty > low.uncertainty}")
    print("note                    : uncertainty is explicit; high uncertainty "
          "prevents trace promotion; contradiction and missing evidence increase "
          "it; reduction must be evidence-linked.")


if __name__ == "__main__":
    main()
