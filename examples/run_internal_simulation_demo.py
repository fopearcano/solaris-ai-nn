#!/usr/bin/env python3
"""Internal simulation demo: simulated sequence + counterfactual, marked non-real.

    python examples/run_internal_simulation_demo.py --state-dir .solaris_ai_nn_cognition/test_internal_simulation

Runs a bounded internal simulation over a sign sequence and a counterfactual
("if sign absent"), and shows that every result is marked simulated / non-real and
is never a live observation.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.semiogenesis import InternalSign, SignKind
from solaris_ai_nn.sensorium_cognition import (
    CounterfactualEngine,
    InternalSimulation,
    SimulationScope,
)


def main():
    parser = argparse.ArgumentParser(description="Internal simulation demo")
    parser.add_argument(
        "--state-dir", type=str,
        default=".solaris_ai_nn_cognition/test_internal_simulation")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    signs = [InternalSign(kind=SignKind.MODALITY_NATIVE, sign_code=f"rf:{i}",
                          modality_distribution={"radio_frequency": 3})
             for i in range(3)]
    refs = [s.sign_id for s in signs]

    sim = InternalSimulation().simulate_sequence(
        refs, SimulationScope.SIGN_SEQUENCE, evidence_refs=["signs"])
    cf = CounterfactualEngine().generate(signs).counterfactuals[0]

    print("=== Internal simulation demo ===")
    print(f"simulation scope      : {sim.scope}")
    print(f"simulation steps      : {sim.step_count if hasattr(sim, 'step_count') else len(sim.steps)}")
    print(f"is_real_observation   : {sim.is_real_observation}")
    print(f"all steps simulated   : {all(s.simulated for s in sim.steps)}")
    print(f"usefulness            : {sim.usefulness} "
          f"(seeds hypothesis: {sim.seeds_hypothesis})")
    print(f"counterfactual        : {cf.form} on {cf.target_ref}")
    print(f"counterfactual is_real: {cf.is_real}")
    print("note: internal simulation and counterfactuals are marked non-real; "
          "they create no external evidence and are never treated as live "
          "observation.")


if __name__ == "__main__":
    main()
