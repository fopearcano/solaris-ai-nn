#!/usr/bin/env python3
"""Pilot-1 daily review demo: a mock day -> daily report + recommendation.

    python examples/run_pilot1_daily_review_demo.py --state-dir .solaris_ai_nn_pilot1/test_daily_review

Builds a daily review from a mock observation rollup, runs ClaimGuard over the
Markdown, and writes day_001.md / day_001.json with a recommended action.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.pilot1 import DailyReviewBuilder


def main() -> None:
    parser = argparse.ArgumentParser(description="Pilot-1 daily review demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_pilot1/test_daily_review")
    args = parser.parse_args()

    builder = DailyReviewBuilder(base_dir=args.state_dir)
    observation = {
        "uptime_ratio": 0.99, "restart_count": 1, "checkpoint_success": 48,
        "memory_size_bytes": 1_200_000, "proto_symbol_count": 12,
        "world_model_node_count": 40, "hypothesis_count": 6,
        "hypothesis_tested_count": 2, "logos_tension_count": 3,
        "autoregeneration_degradation_count": 1, "safety_incident_count": 0,
        "governance_block_count": 0, "drift_velocity": 0.02,
        "stagnation_seconds": 3600.0,
    }
    review = builder.build(1, observation,
                          developmental={"epoch": "infancy"},
                          extra={"major_events": ["first proto-symbol cluster",
                                                  "one graceful restart"],
                                 "active_perception_summary":
                                     "balanced uncertainty sampling"})
    paths = builder.save(review)

    print("=== Pilot-1 daily review demo ===")
    print(f"day            : {review.day_number}")
    print(f"recommendation : {review.recommendation}")
    print(f"claim-guard    : safe={review.claim_guard_safe}")
    print(f"markdown       : {paths['markdown']}")
    print(f"json           : {paths['json']}")


if __name__ == "__main__":
    main()
