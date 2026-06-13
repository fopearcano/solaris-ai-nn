#!/usr/bin/env python3
"""Seasonal-shift demo: slow drift of the world's profile over a long run.

    python examples/run_seasonal_shift_demo.py --steps 800

A seasonal-drift ecology slowly changes its absence/novelty/danger/reward
profile across spring, summer, autumn, and winter. The drift is gradual and
deterministic with the seed; nothing is taught -- the system simply lives
through changing conditions and may adapt its habits and rhythms.
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
    parser = argparse.ArgumentParser(description="Seasonal-shift demo")
    parser.add_argument("--steps", type=int, default=800)
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/seasonal_nursery")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    config = NurseryConfig(
        nursery_id="seasonal-nursery",
        seed=args.seed,
        duration_steps=args.steps,
        seasonal_shift_interval=120,
        active_regimes=[RegimeType.SEASONAL_DRIFT],
        output_state_dir=args.state_dir)
    nursery = DevelopmentalNursery(config=config)

    timeline = []
    last_season = None
    for step in range(args.steps):
        nursery.stimulus_provider(step)
        season = nursery.ecology.seasonality.current_season
        if season != last_season:
            timeline.append((step, season))
            last_season = season
    summary = nursery.summary()

    print("=" * 70)
    print("Solaris-AI-NN -- seasonal-drift nursery (slow change is life)")
    print("=" * 70)
    print(f"steps lived:          {args.steps}")
    print(f"seasonal shifts:      {summary['seasonal_shift_count']}")
    print("season timeline (step -> season):")
    for step, season in timeline:
        print(f"  step {step:>4} -> {season}")
    print("season profiles (multipliers):")
    for season in ("spring", "summer", "autumn", "winter"):
        profile = nursery.ecology.seasonality.profile(season)
        print(f"  {season:8s} absence={profile['absence_mult']:.2f} "
              f"novelty={profile['novelty_mult']:.2f} "
              f"danger={profile['danger_mult']:.2f} "
              f"reward={profile['reward_mult']:.2f}")
    print()

    builder = EcologyReportBuilder(nursery)
    paths = builder.save(
        Path(args.state_dir) / "ecology_report.json",
        Path(args.state_dir) / "ecology_report.md")
    print(f"report: {paths['markdown']} (claim guard safe: "
          f"{paths['claim_guard']['safe']})")
    print()
    print("note: seasonal drift is slow, deterministic, and bounded. It "
          "reshapes the world's probabilities, not the system's goals; no "
          "season carries a label or a lesson.")


if __name__ == "__main__":
    main()
