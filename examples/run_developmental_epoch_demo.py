#!/usr/bin/env python3
"""Developmental epoch demo: a phase/epoch transition from growth.

    python examples/run_developmental_epoch_demo.py --state-dir .solaris_ai_nn_development/test_epoch

Drives a developmental runtime with a sequence of changing module statuses (rising
concept/sign/prediction growth) so that an epoch boundary is opened on a confident
phase transition. Epochs are developmental slices, not biological ages.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.developmental_life import LongHorizonDevelopmentalRuntime


def main():
    parser = argparse.ArgumentParser(description="Developmental epoch demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_development/test_epoch")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    # A mutable status dict; growth metrics rise across ticks.
    ont = {"proto_concept_count": 6, "stable_concept_count": 1,
           "human_label_contamination_score": 0.1}
    sem = {"internal_sign_count": 4, "stable_sign_count": 1,
           "private_syntax_pattern_count": 1}
    cog = {"prediction_success_rate": 0.1, "failed_prediction_count": 1}
    modules = {"perceptual_ontogenesis": ont, "semiogenesis": sem,
               "sensorium_cognition": cog,
               "perceptual_metabolism": {"source_diet_diversity": 0.5}}

    dev = LongHorizonDevelopmentalRuntime(state_dir=args.state_dir,
                                          modules=modules, max_ticks=6,
                                          epoch_tick_span=10)
    for tick in range(6):
        # Growth rises each tick -> a phase transition opens a new epoch.
        ont["stable_concept_count"] = min(8, ont["stable_concept_count"] + 1)
        sem["stable_sign_count"] = min(8, sem["stable_sign_count"] + 1)
        sem["private_syntax_pattern_count"] += 3
        cog["prediction_success_rate"] = min(
            0.9, cog["prediction_success_rate"] + 0.15)
        dev.update(tick=tick)

    status = dev.developmental_status()
    print("=== Developmental epoch demo ===")
    print(f"epochs                : {status['developmental_epoch_count']}")
    print(f"phase transitions     : {status['phase_transition_count']}")
    for e in dev.epochs:
        reason = (e.close_boundary.reason if e.close_boundary
                  else e.open_boundary.reason)
        print(f"  epoch {e.epoch_index}: ticks {e.start_tick}->{e.end_tick} "
              f"reason={reason}")
    print("note: epochs are developmental slices with explainable boundaries, "
          "not biological ages; they are persisted and survive restart.")


if __name__ == "__main__":
    main()
