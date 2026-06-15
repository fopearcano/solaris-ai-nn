#!/usr/bin/env python3
"""Developmental soak short demo: a short bounded stage, checkpoint, packet.

    python examples/run_developmental_soak_short_demo.py --state-dir .solaris_ai_nn_soak/test_short_soak

Runs one short bounded soak stage on fixtures, creates a checkpoint and a daily
evidence packet, compiles a conservative evidence dossier, and writes the
protocol report. Long runs are reached by repeated bounded runs + checkpoints,
never an unbounded daemon. The soak studies structural development, not life.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.developmental_soak import DevelopmentalSoakRuntime


def main():
    parser = argparse.ArgumentParser(description="Developmental soak short demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_soak/test_short_soak")
    args = parser.parse_args()

    rt = DevelopmentalSoakRuntime(
        state_dir=args.state_dir, stage="developmental_soak_30d",
        max_ticks=8, max_runtime_s=25.0)
    rt.run_stage("developmental_soak_30d")
    out = rt.write_artifacts()
    st = rt.soak_status()

    print("=== Developmental soak short demo ===")
    print(f"current stage         : {st['current_stage']}")
    print(f"preflight passed      : {st['preflight_passed']}")
    print(f"checkpoints           : {st['checkpoint_count']} "
          f"(corruption {st['checkpoint_corruption_count']})")
    print(f"daily packets         : {st['daily_packet_count']}")
    print(f"weekly reviews        : {st['weekly_review_count']}")
    print(f"evidence claims       : {st['evidence_claim_count']}")
    print(f"growth verdict        : {st['structural_growth_status']}")
    print(f"safety blocks         : {st['soak_safety_block_count']}")
    print(f"report                : {out['markdown']}")
    print("note                  : the soak protocol studies structural "
          "development through repeated bounded runs; it does not prove life, "
          "consciousness, sentience, personhood, agency, or free will.")


if __name__ == "__main__":
    main()
