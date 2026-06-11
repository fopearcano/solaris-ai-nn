#!/usr/bin/env python3
"""Executive emergency demo: critical state collapses the option space.

    python examples/run_executive_emergency_demo.py

Phase 1: a normal arbitration with a rich candidate field. Phase 2: critical
health forces emergency mode -- the executive may only suggest a checkpoint,
operator review, safe-shutdown recommendation, or nothing, and it provably
cannot talk itself back out of emergency while the condition holds.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.executive import ExecutiveLayer, ExecutiveQueryInterface
from solaris_ai_nn.homeostasis import HomeostaticRegulator


def main() -> None:
    parser = argparse.ArgumentParser(description="Executive emergency demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/exec_emergency")
    args = parser.parse_args()

    regulator = HomeostaticRegulator()
    desires = regulator.update({
        "embodiment": {"energy": 6.0, "max_energy": 10.0,
                       "exhausted": False, "dist_reward": 1.0},
        "latent": {"mysterium_pressure": 0.7,
                   "anticipation_accuracy": 0.5},
    }).desire_candidates

    layer = ExecutiveLayer(state_dir=args.state_dir)

    print("=" * 70)
    print("Solaris-AI-NN -- executive emergency demo")
    print("=" * 70)
    normal = layer.decide(desires, context={"health_level": "ok"}, step=1)
    print(f"phase 1 (healthy):   mode={layer.policy.mode}  "
          f"selected={normal.selected.label!r}  "
          f"candidates={len(normal.scores)}")

    emergency = layer.decide(desires, context={
        "health_level": "critical", "emergency": True,
        "emergency_stop_requested": True}, step=2)
    print(f"phase 2 (critical):  mode={layer.policy.mode}  "
          f"selected={emergency.selected.label!r}")
    survivors = [s.candidate.label for s in emergency.scores
                 if not s.blocked]
    print(f"  surviving options: {survivors}")
    suppressed = [s.candidate.label for s in emergency.scores if s.blocked]
    print(f"  suppressed:        {suppressed[:6]}")

    escape = layer.safety.validate_mode("arbitrated", {"emergency": True})
    print(f"  can leave emergency while it holds: {escape.safe}")
    print(f"  refusal: {escape.violations[0][:74]}")
    print()
    queries = ExecutiveQueryInterface(layer)
    print("Q: what is the executive focus?")
    print(f"A: {queries.answer('what is the executive focus?').text[:160]}")
    print()
    print("note: emergency mode is forced by ops status; only ops/"
          "governance clearing the condition restores normal arbitration.")


if __name__ == "__main__":
    main()
