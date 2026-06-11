#!/usr/bin/env python3
"""Milestone demo: the firsts that mark transformation.

    python examples/run_milestone_demo.py

Simulated context windows trigger first-stable-habit, first Mysterium
spike, and first consolidation; each milestone references its evidence,
fires exactly once, and lands in the autobiographical history and the
fossil-candidate list.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.developmental import (
    AutobiographicalMemory,
    MilestoneDetector,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Milestone demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/milestones")
    args = parser.parse_args()

    detector = MilestoneDetector()
    autobiography = AutobiographicalMemory(state_dir=args.state_dir)

    print("=" * 70)
    print("Solaris-AI-NN -- milestone demo (firsts, with evidence)")
    print("=" * 70)

    windows = [
        ("early window", {"runtime_hours": 2.0,
                          "stable_habit_count": 1}),
        ("after prediction misses", {"runtime_hours": 6.0,
                                     "stable_habit_count": 1,
                                     "major_prediction_failures": 1,
                                     "mysterium_pressure": 0.8}),
        ("after quiet period", {"runtime_hours": 30.0,
                                "stable_habit_count": 2,
                                "consolidation_count": 1}),
        ("repeat of the same window", {"runtime_hours": 31.0,
                                       "stable_habit_count": 2,
                                       "consolidation_count": 2}),
    ]
    for label, context in windows:
        new = detector.detect(context,
                              lifetime_s=context["runtime_hours"] * 3600,
                              simulated=True)
        print(f"{label}:")
        if not new:
            print("  (no new milestones -- each first fires once)")
        for milestone in new:
            autobiography.record_milestone(milestone)
            print(f"  + {milestone.type}")
            print(f"    evidence: {', '.join(milestone.evidence_refs[:3])}")
        print()

    registry = detector.registry
    print(f"registry: {len(registry.milestones)} milestone(s), "
          f"{len(registry.fossil_candidates())} fossil candidate(s)")
    print()
    print("autobiographical history (observational voice):")
    for line in autobiography.as_story().splitlines():
        print(f"  {line}")
    print()
    print(f"history persisted: {autobiography.path}")
    print("note: milestones are recorded firsts with evidence -- "
          "transformation markers, not achievements and not awareness.")


if __name__ == "__main__":
    main()
