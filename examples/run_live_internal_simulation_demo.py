#!/usr/bin/env python3
"""Live internal simulation demo: bounded; no action; no feeder control.

    python examples/run_live_internal_simulation_demo.py --state-dir .solaris_ai_nn_live/sim_demo

Generates bounded internal simulations from anticipations derived from the bundled
safe sign fixture. Simulations are offline metadata only: each is bounded by max
steps, controls no feeders or sources, executes no commands, preserves uncertainty,
and is left as ``not_yet_observed`` pending later live-read-only events.
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
    LiveAnticipationEngine,
    LiveInternalSimulation,
    SignInputLoader,
)

_FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "live_cognition")


def main():
    parser = argparse.ArgumentParser(
        description="Live internal simulation demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/sim_demo")
    parser.add_argument("--max-steps", type=int, default=8, dest="max_steps")
    args = parser.parse_args()

    recs = json.load(open(os.path.join(_FIXTURES,
                                       "sample_live_signs.json")))["records"]
    signs = SignInputLoader().from_records(recs, synthetic=True).eligible
    rhythm = {"patterns": [{"source_id": "machine_body", "kind": "periodic"}]}
    anticipations = LiveAnticipationEngine().anticipate(
        signs=signs, load_status="stable", rhythm=rhythm)
    sims = LiveInternalSimulation(max_steps=args.max_steps).simulate(
        anticipations)

    print("=== Live internal simulation demo ===")
    print(f"  anticipations: {len(anticipations)}; simulations: {len(sims)}")
    for sim in sims:
        d = sim.to_dict()
        print(f"    - {d['simulation_id']} [{d['kind']}] steps={d['step_count']}"
              f" (<= {args.max_steps}) status={d['status']} "
              f"controls_feeders={d['controls_feeders']} "
              f"acts_in_world={d['acts_in_world']}")
    print("note         : internal simulation is bounded offline metadata only; "
          "it controls no feeders or sources, executes no commands, is bounded "
          "by max steps, and is compared against later observed events (here "
          "left as not_yet_observed).")


if __name__ == "__main__":
    main()
