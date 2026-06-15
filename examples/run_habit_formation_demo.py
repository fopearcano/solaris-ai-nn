#!/usr/bin/env python3
"""Habit formation demo: repeated action-effect relation strengthens a habit.

    python examples/run_habit_formation_demo.py --state-dir .solaris_ai_nn_action_reaction/test_habit

Repeatedly reinforces a trigger->action habit from constructive reactions and shows
it strengthening, then weakening when the reaction turns disruptive. Habits are
learned policy tendencies, NOT instincts or will, and remain overrideable.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.action_reaction import HabitFormationEngine, HabitTrigger


def main():
    parser = argparse.ArgumentParser(description="Habit formation demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_action_reaction/test_habit")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    engine = HabitFormationEngine()
    trigger = HabitTrigger.SOURCE_SILENCE_REPEATS

    print("=== Habit formation demo ===")
    for i in range(4):
        h = engine.reinforce(trigger, evidence_ref=f"obs_{i}")
        print(f"  reinforce {i + 1}: strength={h.strength} "
              f"band={h.strength_band} action={h.action_kind}")
    print(f"strengthened habits   : {len(engine.strengthened())}")
    # A disruptive reaction can weaken a habit.
    weak = engine.weaken(trigger)
    print(f"after weakening       : strength={weak.strength} "
          f"band={weak.strength_band}")
    # Safety/governance can always override (inhibit) a habit.
    inhibited = engine.inhibit(trigger)
    print(f"after safety override : inhibited={inhibited.inhibited} "
          f"strength={inhibited.strength}")
    print("note: habits are learned operational policy tendencies, not "
          "instincts, personality, or will; they can be weakened and remain "
          "overrideable by safety/governance.")


if __name__ == "__main__":
    main()
