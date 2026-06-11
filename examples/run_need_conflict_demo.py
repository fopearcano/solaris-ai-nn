#!/usr/bin/env python3
"""Need conflict demo: low energy, near reward, near danger, hard boundary.

    python examples/run_need_conflict_demo.py

One deliberately contradictory situation: the body is nearly exhausted, a
reward marker sits one cell away, a danger marker sits next to it, unknown
pressure is high, and governance requires observe-only. The resolver works
the fixed ladder -- safety first, energy before reward, curiosity last --
and every suppression is recorded with its rule and reason.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.homeostasis import (
    RESOLUTION_PRIORITY,
    HomeostasisQueryInterface,
    HomeostaticRegulator,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Need conflict demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/need_conflict")
    args = parser.parse_args()

    regulator = HomeostaticRegulator(state_dir=args.state_dir)
    result = regulator.update({
        "step": 1,
        "embodiment": {"energy": 0.9, "max_energy": 10.0, "exhausted": True,
                       "dist_reward": 1.0, "dist_danger": 1.5,
                       "blocked_ratio": 0.3},
        "latent": {"mysterium_pressure": 0.8,
                   "anticipation_accuracy": 0.3},
        "blocked_actions": 5,
        "sidecar_attached": True,
        "publish_suggestion_desired": True,
        "valence_events": [{"kind": "danger"}, {"kind": "blocked_action"}],
    })

    print("=" * 70)
    print("Solaris-AI-NN -- need conflict demo")
    print("=" * 70)
    print("the situation: exhausted body, reward 1 cell away, danger close,")
    print("high unknown pressure, blocked actions, observe-only governance")
    print()
    print("needs (pressure):")
    for need in sorted(result.need_state.needs,
                       key=lambda n: -n.intensity)[:7]:
        inhibited = (f"  [inhibited by: {', '.join(need.inhibited_by)}]"
                     if need.inhibited_by else "")
        print(f"  {need.type:24s} intensity={need.intensity:.2f}"
              f"{inhibited}")
    print()
    print(f"resolution ladder: {' > '.join(RESOLUTION_PRIORITY)}")
    print()
    print("conflicts resolved:")
    for conflict in result.conflicts:
        print(f"  {conflict.kind:28s} -> {conflict.winner} "
              f"(rule: {conflict.resolution_rule})")
        print(f"    {conflict.reason[:74]}")
    print()
    print("desire candidates:")
    for candidate in result.desire_candidates:
        mark = "BLOCKED" if candidate.blocked else "ok     "
        print(f"  [{mark}] {candidate.proposal:24s} "
              f"motivation={candidate.motivation:.2f}")
        if candidate.blocked:
            print(f"            reason: {candidate.blocked_reason[:64]}")
    print()
    queries = HomeostasisQueryInterface(regulator)
    print("Q: what conflict blocked action?")
    print(f"A: {queries.answer('what conflict blocked action?').text[:170]}")
    print()
    best = regulator.synthesis.best()
    print(f"surviving suggestion: {best.proposal!r} -- safety and energy "
          "outranked reward and curiosity, exactly per the ladder.")


if __name__ == "__main__":
    main()
