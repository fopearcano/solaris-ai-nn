#!/usr/bin/env python3
"""Weekly review demo: build a weekly review from synthetic daily packets.

    python examples/run_weekly_review_demo.py --state-dir .solaris_ai_nn_soak/test_weekly_review

Builds a week of synthetic daily evidence packets (one showing structural
improvement, one flat) and shows the conservative weekly review decision
(continue / continue-with-warning / inconclusive). Decisions are
recommendation-only -- no automatic external change and no feeder control.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.developmental_soak import (
    DailyEvidencePacketBuilder,
    WeeklyReviewBuilder,
)


def _packet(builder, day, concepts, signs, correct, reactions):
    statuses = {
        "perceptual_ontogenesis": {"stable_concept_count": concepts},
        "semiogenesis": {"useful_sign_count": signs},
        "sensorium_cognition": {"correct_prediction_count": correct},
        "action_reaction": {"reaction_count": reactions},
        "plural_sensorium": {"event_count": 40},
    }
    return builder.build(run_day=day, active_phase="developmental_soak_30d",
                         tick_range=[0, 10], statuses=statuses,
                         dev_status={"structural_growth_status": "inconclusive"})


def main():
    parser = argparse.ArgumentParser(description="Weekly review demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_soak/test_weekly_review")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    builder = DailyEvidencePacketBuilder()
    # A week of packets showing rising concepts/signs/predictions (growth case).
    growth_packets = [
        _packet(builder, d, concepts=2 + d, signs=1 + d, correct=d,
                reactions=d) for d in range(1, 8)]
    # A flat week (accumulation case): nothing structural changes.
    flat_packets = [
        _packet(builder, d, concepts=3, signs=2, correct=1, reactions=1)
        for d in range(1, 8)]

    rb = WeeklyReviewBuilder()
    growth_review = rb.build(week=1, daily_packets=growth_packets)
    flat_review = rb.build(week=2, daily_packets=flat_packets)

    print("=== Weekly review demo ===")
    print(f"growth week decision     : {growth_review.decision}")
    print(f"  rationale              : {growth_review.rationale}")
    print(f"  concepts increased     : "
          f"{growth_review.questions['stable_proto_concepts_increased']}")
    print(f"flat week decision       : {flat_review.decision}")
    print(f"  rationale              : {flat_review.rationale}")
    print(f"  merely accumulated     : "
          f"{flat_review.questions['merely_accumulated_events']}")
    print("note                     : decisions are recommendation-only; no "
          "automatic external change, no feeder control; this does not prove "
          "life or consciousness.")


if __name__ == "__main__":
    main()
