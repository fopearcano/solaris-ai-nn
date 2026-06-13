#!/usr/bin/env python3
"""Developmental nursery demo: a system grows up in a controlled world.

    python examples/run_developmental_nursery_demo.py --steps 600

A developmental system needs an ecology, not a teacher. This runs a bounded
simulated-time developmental run whose *only* input is a
:class:`DevelopmentalNursery`: regimes, day/night and signal/silence cycles,
scarcity, novelty, anomalies, seasonal drift, deprivation windows, and
delayed consequences. Proto-language is enabled so recurring and absent
stimuli can earn internal signs -- with no human teaching, no correct-answer
labels, no LLM, and no real-world action. A ClaimGuard-scanned ecology report
closes the run.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.developmental import DevelopmentalRuntime
from solaris_ai_nn.ecology import EcologyReportBuilder, NurseryConfig
from solaris_ai_nn.ecology.regimes import RegimeType


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Developmental nursery / stimulus ecology demo")
    parser.add_argument("--steps", type=int, default=600)
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/nursery")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    config = NurseryConfig(
        nursery_id="demo-nursery",
        seed=args.seed,
        duration_steps=args.steps,
        active_regimes=[RegimeType.MIXED_NURSERY],
        output_state_dir=args.state_dir)
    runtime = DevelopmentalRuntime(
        state_dir=args.state_dir, simulated_time=True,
        time_acceleration=3600.0, max_steps=args.steps,
        consolidation_interval_steps=100, seed=args.seed,
        enable_ecology=True, nursery_config=config,
        enable_proto_language=True)
    runtime.run()
    nursery = runtime.nursery
    summary = nursery.summary()

    print("=" * 70)
    print("Solaris-AI-NN -- developmental nursery (a world, not a teacher)")
    print("=" * 70)
    print(f"steps lived:          {args.steps} (simulated time)")
    print(f"nursery id:           {summary['nursery_id']}")
    print(f"current regime:       {summary['current_regime']}")
    print(f"current cycle phase:  {summary['current_cycle_phase']}")
    print(f"current season:       {summary['current_season']}")
    print(f"ecology events:       {summary['ecology_event_count']} "
          f"(rate {summary['event_rate']}/step)")
    print(f"absence windows:      {summary['absence_window_count']} "
          f"(rate {summary['absence_rate']})")
    print(f"novelty / anomaly:    {summary['novelty_count']} / "
          f"{summary['anomaly_count']}")
    print(f"delayed groups:       "
          f"{summary['delayed_consequence_group_count']}")
    print(f"seasonal shifts:      {summary['seasonal_shift_count']}")
    print("event distribution:")
    for event_type, count in sorted(nursery.memory.event_counts.items(),
                                    key=lambda kv: -kv[1]):
        print(f"  {event_type:24s} {count}")

    proto = runtime.protolanguage
    if proto is not None:
        psum = proto.summary()
        print(f"proto-symbols emerged: {psum['symbol_count']} "
              f"({psum['stable_symbol_count']} stable)")
    eco_milestones = [m.type for m in runtime.milestones.registry.milestones
                      if "ecology" in m.type or "nursery" in m.type
                      or "seasonal" in m.type or "delayed" in m.type
                      or "deprivation" in m.type or "boundary" in m.type
                      or "anomaly" in m.type]
    print(f"ecology milestones:    {eco_milestones}")
    print()

    builder = EcologyReportBuilder(nursery, developmental=runtime,
                                   protolanguage=proto)
    paths = builder.save(Path(args.state_dir) / "ecology_report.json",
                         Path(args.state_dir) / "ecology_report.md")
    print(f"report: {paths['markdown']} (claim guard safe: "
          f"{paths['claim_guard']['safe']})")
    print()
    print("note: the nursery is a controlled, deterministic, low-compute "
          "stimulus world. Stimuli carry no correct-answer labels and no "
          "human feedback; the system is expected to infer structure from "
          "recurrence, absence, and consequence -- no teacher, no LLM, no "
          "real-world action.")


if __name__ == "__main__":
    main()
