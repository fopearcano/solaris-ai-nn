#!/usr/bin/env python3
"""Live anticipation demo: rhythm, absence, co-occurrence; uncertainty included.

    python examples/run_live_anticipation_demo.py --state-dir .solaris_ai_nn_live/ant_demo

Loads the bundled safe live-sign fixture and generates bounded anticipations
directly: rhythm continuation, continued silence (absence), co-occurrence, and
recurrence -- each carrying explicit uncertainty. Anticipation is internal prediction
metadata only; it requests no data, controls no feeders, and acts in no world.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.live_cognition import LiveAnticipationEngine, SignInputLoader

_FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "live_cognition")


def main():
    parser = argparse.ArgumentParser(description="Live anticipation demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/ant_demo")
    args = parser.parse_args()

    recs = json.load(open(os.path.join(_FIXTURES,
                                       "sample_live_signs.json")))["records"]
    signs = SignInputLoader().from_records(recs, synthetic=True).eligible
    rhythm = {"patterns": [{"source_id": "machine_body", "kind": "periodic"}]}
    anticipations = LiveAnticipationEngine().anticipate(
        signs=signs, load_status="stable", rhythm=rhythm)

    print("=== Live anticipation demo ===")
    print(f"  signs        : {len(signs)}")
    print(f"  anticipations: {len(anticipations)}")
    for a in anticipations:
        d = a.to_dict()
        print(f"    - {d['anticipation_type']:<32} horizon={d['horizon']:<12} "
              f"uncertainty={d['uncertainty']:.2f} status={d['status']}")
    print("note         : anticipation is internal prediction metadata only; it "
          "requests no data, controls no feeders, and acts in no world; "
          "operator-text-only anticipation is blocked; uncertainty is always "
          "included.")


if __name__ == "__main__":
    main()
