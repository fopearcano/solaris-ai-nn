#!/usr/bin/env python3
"""Sensorium cognition demo: signs/concepts -> cognitive moves -> report.

    python examples/run_sensorium_cognition_demo.py --state-dir .solaris_ai_nn_cognition/test_cognition

Feeds a mixed fixture sensorium through ontogenesis (proto-concepts) and
semiogenesis (internal signs) into the cognition runtime, which executes bounded
cognitive moves, predictions, anticipation, question pressure, simulations, and
synthesis, then writes the report. Cognitive moves are operations over signs, NOT
human-language reasoning.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.perceptual_metabolism import PerceptualMetabolismRuntime
from solaris_ai_nn.perceptual_ontogenesis import PerceptualOntogenesisRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.semiogenesis import SemiogenesisRuntime
from solaris_ai_nn.sensorium_cognition import SensoriumCognitionRuntime


def _feeder(base, mod, fn, n=12):
    path = os.path.join(base, f"{fn}.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        for i in range(n):
            fh.write(json.dumps({"modality": mod, "v": 0.6 + 0.3 * (i % 2),
                                 "ts": float(i)}) + "\n")
    return fixture_feeder(f"{fn}_feed", path, mod)


def main():
    parser = argparse.ArgumentParser(description="Sensorium cognition demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_cognition/test_cognition")
    args = parser.parse_args()
    base = args.state_dir
    feeds = os.path.join(base, "feeds")
    os.makedirs(feeds, exist_ok=True)

    sensorium = PluralSensoriumRuntime(state_dir=base)
    sensorium.add_feeder(_feeder(feeds, "alien_rf", "rf"))
    sensorium.add_feeder(_feeder(feeds, "alien_vibration", "vib"))
    sensorium.run_bounded(max_polls=3)

    ont = PerceptualOntogenesisRuntime(state_dir=base, sensorium=sensorium,
                                       max_ticks=6)
    ont.run_bounded()
    sem = SemiogenesisRuntime(state_dir=base, ontogenesis=ont, max_ticks=5)
    sem.run_bounded()
    met = PerceptualMetabolismRuntime(state_dir=base, sensorium=sensorium)
    met.update(events_this_tick=16, tick=0)

    cog = SensoriumCognitionRuntime(state_dir=base, semiogenesis=sem,
                                    ontogenesis=ont, metabolism=met, max_ticks=4)
    cog.run_bounded()
    status = cog.cognition_status()
    out = cog.write_artifacts()

    print("=== Sensorium cognition demo ===")
    print(f"cognitive moves       : {status['cognitive_move_count']}")
    print(f"predictions           : {status['prediction_count']} "
          f"(success rate {status['prediction_success_rate']}, "
          f"failed {status['failed_prediction_count']})")
    print(f"question pressures    : {status['question_pressure_count']}")
    print(f"internal simulations  : {status['internal_simulation_count']} "
          "(marked non-real)")
    print(f"counterfactuals       : {status['counterfactual_count']}")
    print(f"analogies             : {status['analogy_count']}")
    print(f"synthesis events      : {status['synthesis_count']}")
    print(f"attention rec.        : "
          f"{status['cognitive_state']['focus']['attention_recommendation']}")
    print(f"report                : {out['markdown']}")
    print("note                  : cognition is represented as bounded "
          "operational moves over internal signs and proto-concepts, not as "
          "hidden human-language thought; it does not prove understanding or "
          "subjective experience.")


if __name__ == "__main__":
    main()
