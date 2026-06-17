#!/usr/bin/env python3
"""Environmental membrane demo: validated events -> receptors -> impressions.

    python examples/run_environmental_membrane_demo.py --state-dir .solaris_ai_nn_live/membrane_demo

Sets up approved governance, a feeder registry, and a sample inbox of validated
events; runs the bounded environmental membrane runtime; and prints receptor count,
permeability decisions, sensory impression counts, source pressure, and the
recommended downstream phase. The membrane converts validated events into sensory
impressions; it controls no feeders and makes no inner-life claim.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.live_birth import approved_governance, feeder_registry_template
from solaris_ai_nn.environmental_membrane import EnvironmentalMembraneRuntime

_FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "environmental_membrane")


def setup_state(state_dir: str) -> None:
    for sub in ("governance", "feeders", "inbox"):
        os.makedirs(os.path.join(state_dir, sub), exist_ok=True)
    json.dump(approved_governance(), open(os.path.join(
        state_dir, "governance", "LIVE_READONLY_GOVERNANCE.json"), "w"))
    json.dump(feeder_registry_template(), open(os.path.join(
        state_dir, "feeders", "FEEDER_REGISTRY.json"), "w"))
    for fx in ("sample_validated_events.jsonl",
               "sample_contaminated_events.jsonl"):
        src = os.path.join(_FIXTURES, fx)
        if os.path.isfile(src):
            shutil.copy(src, os.path.join(state_dir, "inbox", fx))


def main():
    parser = argparse.ArgumentParser(description="Environmental membrane demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/membrane_demo")
    parser.add_argument("--max-events", type=int, default=500,
                        dest="max_events")
    args = parser.parse_args()

    setup_state(args.state_dir)
    rt = EnvironmentalMembraneRuntime(
        state_dir=args.state_dir, require_governance=True,
        max_events=args.max_events,
        operator_note="bounded environmental membrane (demo)")
    result = rt.run()
    st = rt.membrane_status()

    print("=== Environmental membrane demo ===")
    print(f"  run id              : {st['membrane_run_id']}")
    print(f"  blocked             : {result['blocked']}")
    print(f"  receptors           : {st['membrane_receptor_count']}")
    print(f"  events in           : {st['membrane_event_input_count']}")
    print(f"  sensory impressions : {st['membrane_impression_count']}")
    print(f"  allowed/attenuated  : {st['membrane_allowed_count']} / "
          f"{st['membrane_attenuated_count']}")
    print(f"  blocked/quarantined : {st['membrane_blocked_count']} / "
          f"{st['membrane_quarantined_count']}")
    print(f"  absence impressions : {st['membrane_absence_impression_count']}")
    print(f"  source pressure     : {st['source_pressure_status']} "
          f"(operator dominance {st['membrane_operator_dominance_score']})")
    print(f"  contamination       : {st['membrane_contamination_count']}")
    print(f"  downstream next     : "
          f"{rt.downstream_readiness()['recommended_next_phase']}")
    print(f"  starts feeders/net  : {st['starts_feeders']} / "
          f"{st['accesses_network']}")
    print("note                  : the membrane converts validated read-only "
          "events into sensory impressions. It controls no feeders, accesses no "
          "network, and makes no claim of consciousness, life, or agency.")


if __name__ == "__main__":
    main()
