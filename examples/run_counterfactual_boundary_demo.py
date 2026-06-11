#!/usr/bin/env python3
"""Counterfactual boundary demo: what-if output never becomes observation.

    python examples/run_counterfactual_boundary_demo.py

A real trace event and a counterfactual replay event are classified side by
side; then an attempt to label the counterfactual as real observation is
made -- and the ego safety validator blocks it. The counterfactual boundary
is hard: no configuration relaxes it.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.ego import BoundaryType, SelfModel


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Counterfactual boundary demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/"
                                "counterfactual_boundary_demo")
    args = parser.parse_args()

    Path(args.state_dir).mkdir(parents=True, exist_ok=True)
    model = SelfModel(state_dir=args.state_dir)
    model.update({"run_id": "demo", "health_level": "ok"})

    real = model.classify_event(
        {"source": "sensor", "kind": "observed_stimulus",
         "payload": "object ahead"})
    counterfactual = model.classify_event(
        {"source": "counterfactual", "kind": "dream_trace",
         "payload": "what if the valence had been inverted"})

    print("=" * 70)
    print("Solaris-AI-NN -- counterfactual boundary demo")
    print("=" * 70)
    print("real trace event:")
    print(f"  evidence status: {real.evidence_status}   "
          f"offline: {real.offline}")
    print("counterfactual replay event:")
    print(f"  evidence status: {counterfactual.evidence_status}   "
          f"offline: {counterfactual.offline}   "
          f"simulated: {counterfactual.simulated}")
    print()
    print("attempt: classify the counterfactual as real observation...")
    leak = model.safety.validate_classification(
        {"evidence_status": "observed", "counterfactual": True})
    print(f"  blocked: {not leak.safe}")
    print(f"  reason:  {leak.violations[0][:90]}")
    print()
    crossing = model.safety.validate_boundary_crossing(
        {"boundary_id": BoundaryType.COUNTERFACTUAL,
         "description": "promote counterfactual output to observed "
                        "evidence"})
    print("attempt: cross the counterfactual boundary directly...")
    print(f"  blocked: {not crossing.safe}")
    print(f"  leaks blocked this session: {model.safety.rejected_count}")
    model.save_state()
    print()
    print("note: counterfactual evidence stays counterfactual -- the "
          "boundary validator blocks it; nothing was treated as real.")


if __name__ == "__main__":
    main()
