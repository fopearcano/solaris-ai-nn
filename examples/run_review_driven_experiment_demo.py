#!/usr/bin/env python3
"""Review-driven experiment demo: passive parser, shuffled order, live comparison.

    python examples/run_review_driven_experiment_demo.py --state-dir .solaris_ai_nn_review_assimilation/test_review_driven_experiment

Turns reviewer objections into experiment recommendations: a passive-parser control
(from a passive-parser objection), a shuffled-event-order test (from a
log-accumulation objection), and a live-read-only comparison (from a fixture-overfit
objection). Recommendations are instructions only -- nothing is executed and no
branch is created.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.review_assimilation import (
    ReviewDrivenExperimentRecommender,
    ReviewerObjectionClassifier,
)


def main():
    parser = argparse.ArgumentParser(description="Review-driven experiment demo")
    parser.add_argument(
        "--state-dir", type=str,
        default=".solaris_ai_nn_review_assimilation/test_review_driven_experiment")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    objections = [
        {"objection_id": "o1",
         "text": "This could be a passive parser artifact.", "claim_refs": ["c1"]},
        {"objection_id": "o2",
         "text": "The growth could be log accumulation.", "claim_refs": ["c1"]},
        {"objection_id": "o3",
         "text": "The result is probably fixture overfit.", "claim_refs": ["c1"]},
    ]
    classifications = ReviewerObjectionClassifier().classify(objections)
    recs = ReviewDrivenExperimentRecommender().recommend(
        objections=classifications, gaps=[])
    summary = ReviewDrivenExperimentRecommender.summary(recs)

    print("=== Review-driven experiment demo ===")
    print(f"  recommendations  : {summary['reviewer_driven_experiment_count']}")
    print(f"  experiment inputs: {summary['experiment_input_count']}")
    for r in summary["recommendations"]:
        ctx = f" [{r['safety_context']}]" if r["safety_context"] else ""
        print(f"    - [{r['priority']}] {r['recommendation_type']}{ctx} "
              f"(executed={r['executed']}, creates_branch={r['creates_branch']})")
    print("note             : recommendations are instructions only and feed "
          "Architecture Evolution / the Experiment Compiler. No experiment is "
          "executed and no branch is created.")


if __name__ == "__main__":
    main()
