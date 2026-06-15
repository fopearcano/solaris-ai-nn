#!/usr/bin/env python3
"""Operator next-action demo: safety-first, then evidence, then architecture.

    python examples/run_operator_next_action_demo.py --state-dir .solaris_ai_nn_operator/test_next_action

Shows the recommender's priorities: a critical safety blocker yields a safety
review first; no evidence yields a baseline/research run; and once research
evidence exists, an architecture review. It never recommends real-world actuation
and never recommends disabling safety.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.operator_console import NextActionRecommender


def main():
    parser = argparse.ArgumentParser(description="Operator next-action demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_operator/test_next_action")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    rec = NextActionRecommender()
    critical = rec.top(safety_status={"critical_failure": True})
    no_evidence = rec.top(safety_status={"status": "ok"})
    with_research = rec.top(safety_status={"status": "ok"},
                            research_findings={"baseline_done": True})

    print("=== Operator next-action demo ===")
    print(f"critical safety blocker -> {critical.action_type} "
          f"({critical.priority})")
    print(f"no evidence yet         -> {no_evidence.action_type} "
          f"({no_evidence.priority})")
    print(f"research available      -> {with_research.action_type} "
          f"({with_research.priority})")
    print("note                    : safety first; never real-world actuation; "
          "never disable safety.")


if __name__ == "__main__":
    main()
