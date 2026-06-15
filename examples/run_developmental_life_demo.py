#!/usr/bin/env python3
"""Developmental life demo: a short bounded cycle, epochs, and a report.

    python examples/run_developmental_life_demo.py --state-dir .solaris_ai_nn_development/test_life

Builds a small sensorium-native stack and runs a short bounded developmental cycle:
life-cycle phases, epochs, growth state, maturation markers, and a report.
Developmental life is operational long-horizon trace continuity and structural
change tracking, NOT biological life or consciousness.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.developmental_life import LongHorizonDevelopmentalRuntime
from solaris_ai_nn.perceptual_metabolism import PerceptualMetabolismRuntime
from solaris_ai_nn.perceptual_ontogenesis import PerceptualOntogenesisRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.semiogenesis import SemiogenesisRuntime
from solaris_ai_nn.sensorium_cognition import SensoriumCognitionRuntime
from solaris_ai_nn.self_boundary import SelfBoundaryRuntime


def _feeder(base, mod, fn, n=12):
    path = os.path.join(base, f"{fn}.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        for i in range(n):
            fh.write(json.dumps({"modality": mod, "v": 0.6 + 0.3 * (i % 2),
                                 "ts": float(i)}) + "\n")
    return fixture_feeder(f"{fn}_feed", path, mod)


def main():
    parser = argparse.ArgumentParser(description="Developmental life demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_development/test_life")
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
                                    ontogenesis=ont, max_ticks=2)
    cog.run_bounded()
    sb = SelfBoundaryRuntime(state_dir=base, sensorium=sensorium, max_ticks=2)
    sb.run_bounded()

    dev = LongHorizonDevelopmentalRuntime(
        state_dir=base,
        modules={"plural_sensorium": sensorium, "perceptual_metabolism": met,
                 "perceptual_ontogenesis": ont, "semiogenesis": sem,
                 "sensorium_cognition": cog, "self_boundary": sb},
        max_ticks=8, epoch_tick_span=3)
    dev.run_bounded()
    status = dev.developmental_status()
    out = dev.write_artifacts()

    print("=== Developmental life demo ===")
    print(f"life-cycle phase      : {status['current_life_cycle_phase']} "
          f"({status['life_cycle_phase_count']} visited)")
    print(f"epochs                : {status['developmental_epoch_count']}")
    print(f"maturation markers    : {status['maturation_marker_count']}")
    print(f"phase transitions     : {status['phase_transition_count']}")
    print(f"plateaus              : {status['plateau_count']}")
    print(f"regressions           : {status['regression_count']}")
    print(f"structural growth     : {status['structural_growth_status']} "
          f"(score {status['structural_growth_score']})")
    print(f"report                : {out['markdown']}")
    print("note                  : developmental life is operational long-horizon "
          "trace continuity and structural change tracking; it is not a claim of "
          "biological life, consciousness, sentience, personhood, agency, or "
          "free will.")


if __name__ == "__main__":
    main()
