#!/usr/bin/env python3
"""Run the Pilot-0 Solaris sidecar observation against a FAKE runtime.

    python examples/run_pilot_sidecar_fake.py --steps 100

Observe-only throughout: the fake Conscience's bus is watched, signals are
mirrored into the substrate, suggestions are produced but never published,
and the fake runtime is never driven (no stimulate/react/death calls).
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.experiments.solaris_sidecar_observation import (
    FakeConscience,
    Reaction,
    Stimulus,
)
from solaris_ai_nn.pilot import PilotDeploymentRunner, PilotManifest

PAYLOADS = ["light", "noise", "food", "silence"]


def driver(conscience, step: int) -> None:
    """The fake organism living its life; the sidecar only watches."""
    conscience.bus.publish(Stimulus(payload=PAYLOADS[step % 4],
                                    intensity=0.4 + 0.1 * (step % 5)))
    if step % 4 == 2:
        conscience.bus.publish(Reaction(valence=1.0 if step % 8 == 2
                                        else -0.5))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pilot-0 sidecar observation (fake runtime, bounded)")
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/pilot_sidecar")
    parser.add_argument("--artifact-dir", type=str,
                        default=".solaris_ai_nn_pilots")
    parser.add_argument("--operator", type=str, default="local-operator")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    conscience = FakeConscience()
    manifest = PilotManifest(
        profile="solaris_sidecar_observe", operator=args.operator,
        state_dir=args.state_dir, artifact_dir=args.artifact_dir,
        max_steps=args.steps, seed=args.seed,
        notes="Pilot-0 sidecar observation example (fake runtime)")
    # The operator passed these directories explicitly: that is the approval.
    runner = PilotDeploymentRunner(
        manifest=manifest, conscience=conscience, sidecar_driver=driver,
        approved_output_roots=[args.state_dir, args.artifact_dir])
    for name in runner.acknowledge_risks(
            note="reviewed in run_pilot_sidecar_fake example"):
        print(f"operator {args.operator!r} acknowledged risk: {name}")

    snapshot = runner.run()
    entry = snapshot["registry_entry"] or {}
    sidecar = runner.adapter.sidecar
    print("=" * 70)
    print("Solaris-AI-NN -- Pilot-0 sidecar observation (fake runtime)")
    print("=" * 70)
    print(f"pilot_id:           {manifest.pilot_id}")
    print(f"status:             {entry.get('status')}")
    print(f"steps observed:     {runner.adapter.steps_observed}")
    if sidecar is not None:
        state = sidecar.state
        print(f"signals observed:   {state.signals_observed}")
        print(f"suggestions made:   {state.suggestions_produced}")
        print(f"suggestions published: {state.suggestions_published} "
              "(publishing requires separate approval)")
    print(f"conscience driven:  stimulate={conscience.stimulate_calls} "
          f"react={conscience.react_calls} death={conscience.death_calls}")
    print(f"recommendation:     {entry.get('final_recommendation')}")
    print(f"pilot report:       {entry.get('report_path')}")
    if snapshot["refused"]:
        print("refused because:")
        for reason in snapshot["refusal_reasons"]:
            print(f"  - {reason}")


if __name__ == "__main__":
    main()
