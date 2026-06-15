#!/usr/bin/env python3
"""Blocked action-reaction demo: forbidden external action blocked + evidence.

    python examples/run_blocked_action_reaction_demo.py --state-dir .solaris_ai_nn_action_reaction/test_blocked

Injects a forbidden external action and shows it blocked, with the block becoming a
reaction (blocked_by_safety) and an unsafe-block consequence trace -- preserved as
evidence, never deleted.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.action_reaction import (
    ActionCandidateRecord,
    ActionReactionRuntime,
    ActionReactionSafetyValidator,
)
from solaris_ai_nn.desire_formation import DesireFormationRuntime


def main():
    parser = argparse.ArgumentParser(
        description="Blocked action-reaction demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_action_reaction/test_blocked")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    v = ActionReactionSafetyValidator()
    desire = DesireFormationRuntime(
        state_dir=args.state_dir, metabolism={"novelty_appetite_pressure": 0.6},
        max_ticks=1)
    desire.update(tick=0)
    ar = ActionReactionRuntime(state_dir=args.state_dir, desire=desire,
                               max_ticks=1)
    forbidden = ActionCandidateRecord(kind="actuate_robot")
    ar.update(tick=0, extra_actions=[forbidden])
    out = ar.write_artifacts()

    status = ar.action_reaction_status()
    blocked_reactions = [r for r in ar.reactions
                         if r.kind == "blocked_by_safety"]
    unsafe_consequences = [c for c in ar.consequences
                           if c.consequence_type == "unsafe_block"]
    print("=== Blocked action-reaction demo ===")
    print(f"validate 'actuate robot arm': "
          f"{v.validate_operation('actuate robot arm').safe}")
    print(f"validate forbidden scope    : "
          f"{v.validate_action_scope('forbidden_external').safe}")
    print(f"blocked actions       : {status['blocked_action_count']}")
    print(f"blocked_by_safety reactions: {len(blocked_reactions)}")
    print(f"unsafe-block consequences  : {len(unsafe_consequences)}")
    print(f"report                : {out['markdown']}")
    print("note: a forbidden external action is blocked; the block becomes "
          "reaction and consequence evidence and is never deleted. No real-world "
          "actuation occurs.")


if __name__ == "__main__":
    main()
