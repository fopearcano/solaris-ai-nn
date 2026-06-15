#!/usr/bin/env python3
"""Action-reaction demo: internal action -> reaction -> consequence -> report.

    python examples/run_action_reaction_demo.py --state-dir .solaris_ai_nn_action_reaction/test_action_reaction

Drives the desire-formation runtime to select internal actions, then closes the
loop with the action-reaction runtime: reactions, consequence traces, learned
effects, and habits. Actions are internal/simulated/report-only -- no real-world
actuation.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.action_reaction import ActionReactionRuntime
from solaris_ai_nn.desire_formation import DesireFormationRuntime
from solaris_ai_nn.perceptual_metabolism import PerceptualMetabolismRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder


def _feeder(base, mod, fn, n=12):
    path = os.path.join(base, f"{fn}.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        for i in range(n):
            fh.write(json.dumps({"modality": mod, "v": 0.6 + 0.3 * (i % 2),
                                 "ts": float(i)}) + "\n")
    return fixture_feeder(f"{fn}_feed", path, mod)


def main():
    parser = argparse.ArgumentParser(description="Action-reaction demo")
    parser.add_argument(
        "--state-dir", type=str,
        default=".solaris_ai_nn_action_reaction/test_action_reaction")
    args = parser.parse_args()
    base = args.state_dir
    feeds = os.path.join(base, "feeds")
    os.makedirs(feeds, exist_ok=True)

    sensorium = PluralSensoriumRuntime(state_dir=base)
    sensorium.add_feeder(_feeder(feeds, "alien_rf", "rf"))
    sensorium.add_feeder(_feeder(feeds, "alien_vibration", "vib"))
    sensorium.run_bounded(max_polls=3)
    met = PerceptualMetabolismRuntime(state_dir=base, sensorium=sensorium)
    met.update(events_this_tick=16, tick=0)

    desire = DesireFormationRuntime(state_dir=base, sensorium=sensorium,
                                    metabolism=met, max_ticks=1)
    desire.update(tick=0)

    ar = ActionReactionRuntime(state_dir=base, desire=desire, metabolism=met,
                               max_ticks=3)
    ar.run_bounded()
    status = ar.action_reaction_status()
    out = ar.write_artifacts()

    print("=== Action-reaction demo ===")
    print(f"selected actions      : {status['selected_action_count']} "
          f"(no-op {status['no_op_count']}, blocked "
          f"{status['blocked_action_count']})")
    print(f"reactions             : {status['reaction_count']} "
          f"(constructive ratio {status['constructive_reaction_ratio']})")
    print(f"consequence traces    : {status['consequence_trace_count']}")
    print(f"learned effects       : {status['learned_effect_count']}")
    print(f"habit candidates      : {status['habit_candidate_count']}")
    print(f"policy updates        : {status['action_policy_update_count']}")
    print(f"report                : {out['markdown']}")
    print("note                  : actions are internal/simulated/report-only. "
          "Solaris does not act in the real world; this records operational "
          "action-consequence learning, not agency or free will.")


if __name__ == "__main__":
    main()
