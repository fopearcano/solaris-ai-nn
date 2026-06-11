#!/usr/bin/env python3
"""Drift/growth demo: structural change vs stagnation, drift vs inertia.

    python examples/run_drift_growth_demo.py

Three scripted trajectories: structural growth (schemas consolidate),
stagnation (nothing moves), and a sudden jump that becomes a
phase-transition *candidate* -- a hypothesis with before/after numbers,
never an emergence claim.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.developmental import (
    GrowthMonitor,
    LongRunDriftMonitor,
    PhaseTransitionDetector,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Drift/growth demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/drift_growth")
    args = parser.parse_args()
    del args  # nothing persists in this demo

    print("=" * 70)
    print("Solaris-AI-NN -- drift/growth demo (measured, not assumed)")
    print("=" * 70)

    growth = GrowthMonitor()
    windows = [
        ("baseline", {"world_model_node_count": 10,
                      "stable_habit_count": 2,
                      "consolidated_schema_count": 0}),
        ("data accumulates", {"world_model_node_count": 40,
                              "stable_habit_count": 2,
                              "consolidated_schema_count": 0}),
        ("structure consolidates", {"world_model_node_count": 45,
                                    "stable_habit_count": 4,
                                    "consolidated_schema_count": 3}),
        ("nothing moves", {"world_model_node_count": 45,
                           "stable_habit_count": 4,
                           "consolidated_schema_count": 3}),
        ("still nothing", {"world_model_node_count": 45,
                           "stable_habit_count": 4,
                           "consolidated_schema_count": 3}),
    ]
    print("growth windows:")
    for label, metrics in windows:
        snapshot = growth.observe(metrics)
        print(f"  {label:24s} -> {snapshot.classification:14s} "
              f"(structural change {snapshot.structural_change_score})")
    print(f"  stagnation windows: {growth.stagnation_windows}")
    print()

    drift = LongRunDriftMonitor()
    drift.observe({"substrate_state_norm": 4.0, "mysterium_pressure": 0.4})
    slow = drift.observe({"substrate_state_norm": 4.2,
                          "mysterium_pressure": 0.38})
    fast = drift.observe({"substrate_state_norm": 12.0,
                          "mysterium_pressure": 0.9})
    print("drift windows:")
    print(f"  slow adaptation -> {slow.classification} "
          f"(velocity {slow.drift_velocity})")
    print(f"  sudden movement -> {fast.classification}")
    for warning in fast.warnings:
        print(f"    warning: {warning[:80]}")
    print()

    phases = PhaseTransitionDetector()
    phases.observe({"prediction_accuracy": 0.45,
                    "mysterium_pressure": 0.6})
    candidates = phases.observe({"prediction_accuracy": 0.85,
                                 "mysterium_pressure": 0.15})
    print("phase-transition candidates:")
    for candidate in candidates:
        print(f"  {candidate.kind}: {candidate.metric} "
              f"{candidate.before} -> {candidate.after} "
              f"(confidence {candidate.confidence})")
        print(f"    {candidate.note}")
    print()
    print("note: growth labels, drift verdicts, and phase-transition "
          "candidates are measurements over recorded metrics -- "
          "structural change is measured, never assumed.")


if __name__ == "__main__":
    main()
