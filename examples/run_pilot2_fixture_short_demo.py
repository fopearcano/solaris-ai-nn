#!/usr/bin/env python3
"""Pilot-2 fixture short demo: a bounded read-only fixture sensory exposure.

    python examples/run_pilot2_fixture_short_demo.py --state-dir .solaris_ai_nn_pilot2/test_fixture_short

Runs a short bounded fixture exposure through the read-only sensory membrane,
tracks per-source reliability, and prints a daily review. No real sources, no
actuation; the system never acts on the fixtures.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.pilot2 import (
    Pilot2DailyReviewBuilder,
    SourceReliabilityMonitor,
)
from solaris_ai_nn.sensory_membrane import (
    SensoryMembraneRuntime,
    SensorySourceConfig,
)


def main():
    parser = argparse.ArgumentParser(description="Pilot-2 fixture short demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_pilot2/test_fixture_short")
    args = parser.parse_args()

    root = os.path.join(args.state_dir, "inputs")
    state = os.path.join(args.state_dir, "state")
    os.makedirs(root, exist_ok=True)
    jp = os.path.join(root, "events.jsonl")
    open(jp, "w").write("".join('{"evt":"ping","i":%d}\n' % i
                                for i in range(6)))

    rt = SensoryMembraneRuntime(
        state_dir=state, allowed_input_roots=[root], enabled=True,
        simulated_sources_only=False, real_read_only_sources_enabled=True)
    rt.add_source(SensorySourceConfig(source_id="j", source_type="jsonl_file",
                                      path=jp, enabled=True))
    rt.initialize()
    rt.run_bounded(max_polls=3)

    monitor = SourceReliabilityMonitor()
    s = rt.summary()
    monitor.observe_poll("j", success=True, events=s["total_events"],
                         provenance=s["total_events"], usefulness=0.4)

    review = Pilot2DailyReviewBuilder(base_dir=args.state_dir).build(
        1, {"event_count": s["total_events"], "provenance_completeness":
            s["provenance_completeness"], "source_status": {"j": "reliable"},
            "new_sensory_proto_symbols":
            rt.grounding.snapshot()["proto_symbol_candidate_count"]})
    paths = Pilot2DailyReviewBuilder(base_dir=args.state_dir).save(review)

    print("=== Pilot-2 fixture short demo ===")
    print(f"events ingested : {s['total_events']}")
    print(f"provenance      : {s['provenance_completeness']}")
    print(f"reliability      : {monitor.by_class()}")
    print(f"daily review     : {paths['markdown']}")
    print(f"recommendation   : {review.recommendation}")


if __name__ == "__main__":
    main()
