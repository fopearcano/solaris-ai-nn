#!/usr/bin/env python3
"""Deprivation nursery demo: long quiet, scarcity, and recovery.

    python examples/run_deprivation_nursery_demo.py --steps 400

A sparse, deprivation-heavy ecology: long silence, scarcity events, and
absence windows dominate, with recoverable disruptions. When the nursery
emits an absence, the stimulus provider returns ``None`` -- so the runner's
own absence/continuity machinery (the latent "I exist!" pathway) takes over.
This exercises latent activation during deprivation. No teaching, no labels.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.ecology import (
    DevelopmentalNursery,
    EcologyReportBuilder,
    NurseryConfig,
)
from solaris_ai_nn.ecology.regimes import RegimeType


def main() -> None:
    parser = argparse.ArgumentParser(description="Deprivation nursery demo")
    parser.add_argument("--steps", type=int, default=400)
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/deprivation_nursery")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    config = NurseryConfig(
        nursery_id="deprivation-nursery",
        seed=args.seed,
        duration_steps=args.steps,
        absence_rate=0.55,
        scarcity_rate=0.5,
        active_regimes=[RegimeType.SPARSE_DESERT],
        output_state_dir=args.state_dir)
    nursery = DevelopmentalNursery(config=config)

    silences = 0
    signals = 0
    for step in range(args.steps):
        if nursery.stimulus_provider(step) is None:
            silences += 1
        else:
            signals += 1
    summary = nursery.summary()
    mem = nursery.memory.snapshot()

    print("=" * 70)
    print("Solaris-AI-NN -- deprivation nursery (scarcity, silence, "
          "recovery)")
    print("=" * 70)
    print(f"steps lived:          {args.steps}")
    print(f"silent steps:         {silences} (provider returned None)")
    print(f"signal steps:         {signals}")
    print(f"absence windows:      {summary['absence_window_count']} "
          f"(rate {summary['absence_rate']})")
    print(f"deprivation windows:  {mem['deprivation_windows']}")
    print(f"scarcity events:      "
          f"{nursery.memory.event_counts.get('scarcity_event', 0)}")
    scarcity = nursery.ecology.scarcity.pressures()
    print("scarcity pressures:")
    for name, value in scarcity.items():
        print(f"  {name:24s} {value}")
    print()

    builder = EcologyReportBuilder(nursery)
    paths = builder.save(
        Path(args.state_dir) / "ecology_report.json",
        Path(args.state_dir) / "ecology_report.md")
    print(f"report: {paths['markdown']} (claim guard safe: "
          f"{paths['claim_guard']['safe']})")
    print()
    print("note: deprivation windows are controlled, bounded, recoverable "
          "perturbations -- not errors and not punishment. Silence returns "
          "no stimulus so the system's own continuity machinery activates.")


if __name__ == "__main__":
    main()
