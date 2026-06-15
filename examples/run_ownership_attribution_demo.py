#!/usr/bin/env python3
"""Ownership attribution demo: internal, external feeder, memory, sim, ambiguous.

    python examples/run_ownership_attribution_demo.py --state-dir .solaris_ai_nn_self_boundary/test_ownership

Attributes ownership of five record kinds and shows that processed sensory input is
not "self", a feeder event is external, a simulation is internal-simulation (not
real), and ambiguous attribution is preserved.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.self_boundary import OwnershipAttributor, OwnershipType


def main():
    parser = argparse.ArgumentParser(description="Ownership attribution demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_self_boundary/test_ownership")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    attributor = OwnershipAttributor()
    cases = [
        ("internal_metabolic", "metabolism_state"),
        ("external_feeder", "rf_feed_event"),
        ("memory_replay", "trace_42"),
        ("internal_simulation", "sim_07"),
        ("ambiguous", "unknown_blob"),
    ]
    print("=== Ownership attribution demo ===")
    for kind, ref in cases:
        att = attributor.attribute(kind, ref, confidence=0.6)
        print(f"  {ref:18s} -> {att.ownership_type:24s} "
              f"zone={att.zone} is_self={att.is_self}")
    print(f"distribution          : {attributor.distribution()}")
    print(f"ambiguous (preserved) : {len(attributor.ambiguous())}")
    # An external feeder event is NOT self even though Solaris processed it.
    feeder = [a for a in attributor.attributions
              if a.ownership_type == OwnershipType.EXTERNAL_FEEDER_ARTIFACT][0]
    print(f"feeder event is_self  : {feeder.is_self} (external, not self)")
    print("note: sensory input is not 'self' merely because Solaris processed "
          "it; internal simulation is not the real world; operator annotation "
          "is not ground truth; ambiguous attribution is preserved.")


if __name__ == "__main__":
    main()
