#!/usr/bin/env python3
"""Human-vs-non-human sensorium demo: different senses -> different structure.

    python examples/run_human_vs_nonhuman_sensorium_demo.py --state-dir .solaris_ai_nn_state/test_human_vs_nonhuman

Runs three sensoria over the same number of events -- human-like-only,
non-human-only, and mixed -- and compares the internal structures that emerge
(modalities, invariants, cross-modal relations). Human-like senses are valid but
not privileged.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder


def _write(path, modality, n=8):
    with open(path, "w", encoding="utf-8") as fh:
        for i in range(n):
            fh.write(json.dumps({"modality": modality, "v": 0.4 + 0.4 * (i % 2),
                                 "ts": float(i)}) + "\n")


def _run(base, name, modalities):
    feeds = os.path.join(base, name)
    os.makedirs(feeds, exist_ok=True)
    rt = PluralSensoriumRuntime(state_dir=os.path.join(base, name + "_state"))
    for mod in modalities:
        path = os.path.join(feeds, f"{mod}.jsonl")
        _write(path, mod)
        rt.add_feeder(fixture_feeder(f"{mod}_feed", path, mod))
    rt.run_bounded(max_polls=1)
    return rt.plural_sensorium_status()


def main():
    parser = argparse.ArgumentParser(description="Human vs non-human sensorium")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/test_human_vs_nonhuman")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    human = _run(args.state_dir, "human", ["human_textual"])
    nonhuman = _run(args.state_dir, "nonhuman", ["alien_rf", "alien_echo"])
    mixed = _run(args.state_dir, "mixed",
                 ["human_textual", "alien_rf", "alien_echo"])

    print("=== Human vs non-human sensorium demo ===")
    for label, st in (("human-like-only", human), ("non-human-only", nonhuman),
                      ("mixed", mixed)):
        print(f"{label:>16}: modalities={st['active_modality_count']} "
              f"invariants={st['invariant_candidate_count']} "
              f"cross_modal={st['cross_modal_relation_count']}")
    differ = (human['active_modality_count'] != nonhuman['active_modality_count']
              or mixed['cross_modal_relation_count']
              > human['cross_modal_relation_count'])
    print(f"different internal structures: {differ}")
    print("note                  : human senses are valid but not privileged; "
          "the question is what structure each sensorium yields.")


if __name__ == "__main__":
    main()
