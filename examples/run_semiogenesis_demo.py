#!/usr/bin/env python3
"""Semiogenesis demo: proto-concepts -> internal signs -> sign report.

    python examples/run_semiogenesis_demo.py --state-dir .solaris_ai_nn_semiogenesis/test_semiogenesis

Feeds a mixed fixture sensorium through ontogenesis (proto-concepts) into the
semiogenesis runtime, which conservatively births internal signs, clusters them
into families, derives a private syntax, composes internal utterances, and writes
the report. Signs are operational markers, NOT human words.
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
from solaris_ai_nn.semiogenesis import SemiogenesisRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder


def _feeder(base, mod, fn, n=12):
    path = os.path.join(base, f"{fn}.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        for i in range(n):
            fh.write(json.dumps({"modality": mod, "v": 0.6 + 0.3 * (i % 2),
                                 "ts": float(i)}) + "\n")
    return fixture_feeder(f"{fn}_feed", path, mod)


def main():
    parser = argparse.ArgumentParser(description="Semiogenesis demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_semiogenesis/test_semiogenesis")
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
    met = PerceptualMetabolismRuntime(state_dir=base, sensorium=sensorium)
    met.update(events_this_tick=16, tick=0)

    sem = SemiogenesisRuntime(state_dir=base, ontogenesis=ont, metabolism=met,
                              max_ticks=5)
    sem.run_bounded()
    status = sem.semiogenesis_status()
    out = sem.write_artifacts()

    print("=== Semiogenesis demo ===")
    print(f"internal signs        : {status['internal_sign_count']} "
          f"(stable {status['stable_sign_count']})")
    print(f"sign families         : {status['sign_family_count']} "
          f"(dominant {status['dominant_sign_family']})")
    print(f"private syntax patterns: {status['private_syntax_pattern_count']}")
    print(f"internal utterances   : {status['internal_utterance_count']}")
    print(f"modality-native ratio : {status['modality_native_sign_ratio']}")
    print(f"contaminated ratio    : {status['contaminated_sign_ratio']}")
    print(f"gloss dependence      : {status['gloss_dependence_score']}")
    sample = list(sem.signs.values())[:4]
    print(f"sample sign codes     : {[s.sign_code for s in sample]}")
    print(f"report                : {out['markdown']}")
    print("note                  : signs are operational markers grounded in "
          "perceptual structures, not human words; human-readable gloss is an "
          "approximate debug annotation, not the sign itself.")


if __name__ == "__main__":
    main()
