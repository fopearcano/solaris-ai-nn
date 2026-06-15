#!/usr/bin/env python3
"""Source diet demo: human-like-dominated vs non-human-dominated vs mixed.

    python examples/run_source_diet_demo.py --state-dir .solaris_ai_nn_state/test_source_diet

Runs three sensoria with different source diets and reports the diet balance for
each: diversity, modality dominance, human-label dominance, and non-human
contribution. Human-like, non-human, and mixed diets are all allowed; dominance is
measured, never hidden.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.perceptual_metabolism import SourceDietAnalyzer
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder


def _run(base, name, modalities, labelled=False):
    feeds = os.path.join(base, name)
    os.makedirs(feeds, exist_ok=True)
    rt = PluralSensoriumRuntime(state_dir=os.path.join(base, name + "_state"))
    for mod in modalities:
        path = os.path.join(feeds, f"{mod}.jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            for i in range(8):
                rec = {"modality": mod, "v": 0.6, "ts": float(i)}
                if labelled and mod == "human_textual":
                    rec["annotation"] = f"obs {i}"
                    rec["annotation_status"] = "human_label_external"
                fh.write(json.dumps(rec) + "\n")
        rt.add_feeder(fixture_feeder(f"{mod}_feed", path, mod))
    rt.run_bounded(max_polls=1)
    return SourceDietAnalyzer().analyze(rt)


def main():
    parser = argparse.ArgumentParser(description="Source diet demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/test_source_diet")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    human = _run(args.state_dir, "human", ["human_textual"], labelled=True)
    nonhuman = _run(args.state_dir, "nonhuman",
                    ["alien_rf", "alien_echo", "vibration"])
    mixed = _run(args.state_dir, "mixed",
                 ["human_textual", "alien_rf", "vibration"])

    print("=== Source diet demo ===")
    for label, diet in (("human-dominated", human),
                        ("non-human-dominated", nonhuman),
                        ("mixed", mixed)):
        print(f"{label:>20}: diversity={diet.diet_diversity} "
              f"dominance={diet.modality_dominance} "
              f"human_label={diet.human_label_dominance} "
              f"non_human={diet.non_human_contribution} "
              f"dominant_class={diet.dominant_class}")
    print("note                  : human-like, non-human, and mixed diets are "
          "all allowed; dominance is measured, never hidden.")


if __name__ == "__main__":
    main()
