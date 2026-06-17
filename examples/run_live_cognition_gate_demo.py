#!/usr/bin/env python3
"""Live cognition gate demo: ready, blocked by weak signs / label / contradiction.

    python examples/run_live_cognition_gate_demo.py --state-dir .solaris_ai_nn_live/cgate_demo

Runs the cognition pipeline directly (with already-trusted sign inputs) over several
scenarios and prints the advisory cognition readiness gate decision for each: ready
(trace/anticipation), blocked by too few stable signs, blocked by label dependence,
and blocked by prediction contradiction. The gate is advisory -- it enables no
action, autonomy, or self-boundary tracking.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.live_cognition import (
    FirstLiveCognitionRuntime,
    SignInputLoader,
)

_FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "live_cognition")


def _signs(name):
    recs = json.load(open(os.path.join(_FIXTURES, name)))["records"]
    return SignInputLoader().from_records(recs, synthetic=True)


def _run(state_dir, signs, later_events=None):
    rt = FirstLiveCognitionRuntime(
        state_dir=state_dir,
        profile="live_cognition_anticipation_limited_v0")
    rt.analyze_signs(signs, later_events=later_events)
    return rt.readiness


def main():
    parser = argparse.ArgumentParser(description="Live cognition gate demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/cgate_demo")
    args = parser.parse_args()

    safe = _signs("sample_live_signs.json")
    contaminated = _signs("sample_contaminated_cognition.json")

    print("=== Live cognition gate demo ===")
    # Ready (enough stable signs, clean).
    g = _run(args.state_dir + "/ready", safe.eligible)
    print(f"  ready scenario       : {g['cognition_readiness_status']} "
          f"-> {g['recommended_next_phase']}")
    # Blocked by too few stable signs (one sign only).
    g = _run(args.state_dir + "/weak", safe.eligible[:1])
    print(f"  weak-signs scenario  : {g['cognition_readiness_status']}")
    # Blocked by label/operator dependence (contaminated signs).
    g = _run(args.state_dir + "/contaminated", contaminated.signs)
    print(f"  contaminated scenario: {g['cognition_readiness_status']}")
    for b in g.get("blockers", []):
        print(f"      blocker: {b['blocker']} -> {b['correction']}")
    print("note: the cognition readiness gate is advisory; it enables no action, "
          "autonomy, or self-boundary tracking; it creates only operational "
          "cognition-readiness records.")


if __name__ == "__main__":
    main()
