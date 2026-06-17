#!/usr/bin/env python3
"""Permeability demo: allow, attenuate, block, quarantine, create absence.

    python examples/run_permeability_demo.py --state-dir .solaris_ai_nn_live/perm_demo

Feeds the contaminated + validated fixtures directly to the membrane (component path)
and prints the permeability decision per event: allow / allow_attenuated / block /
quarantine, plus absence-impression creation. The membrane says more than
valid/invalid, and every decision is explained.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.environmental_membrane import EnvironmentalMembraneRuntime

_FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "environmental_membrane")


def _load(name):
    path = os.path.join(_FIXTURES, name)
    return [json.loads(l) for l in open(path)] if os.path.isfile(path) else []


def main():
    parser = argparse.ArgumentParser(description="Permeability demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/perm_demo")
    args = parser.parse_args()

    events = (_load("sample_validated_events.jsonl")
              + _load("sample_contaminated_events.jsonl"))
    rt = EnvironmentalMembraneRuntime(state_dir=args.state_dir,
                                      profile="fixture_membrane_v0")
    rt.analyze_events(events)

    print("=== Permeability demo ===")
    seen = set()
    for d in rt.permeability_decisions:
        seen.add(d["status"])
        absent = " [creates absence impression]" if d["creates_absence"] else ""
        print(f"  {d['source_id']:<28} -> {d['status']}{absent} "
              f"-- {(d['reasons'][:1] or [''])[0]}")
    print(f"  distinct statuses observed: {sorted(seen)}")
    print("note: the membrane says allowed/blocked/attenuated/amplified/deferred/"
          "quarantined -- not merely valid/invalid; blocked and quarantined "
          "impressions are visible, never hidden.")


if __name__ == "__main__":
    main()
