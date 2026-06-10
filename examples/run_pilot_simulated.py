#!/usr/bin/env python3
"""Run the Pilot-0 simulated deployment (the safe default profile).

    python examples/run_pilot_simulated.py --steps 100
    python examples/run_pilot_simulated.py --language --substrate liquid_state

Everything happens inside the GridWorld sandbox: governed, supervised,
bounded, with a readiness report before and a pilot report after.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.pilot import PilotDeploymentRunner, PilotManifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Pilot-0 simulated (bounded)")
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/pilot_simulated")
    parser.add_argument("--artifact-dir", type=str,
                        default=".solaris_ai_nn_pilots")
    parser.add_argument("--operator", type=str, default="local-operator")
    parser.add_argument("--substrate", type=str, default="esn",
                        choices=["esn", "liquid_state", "spiking_recurrent"])
    parser.add_argument("--language", action="store_true")
    parser.add_argument("--enable-plasticity-dry-run", action="store_true")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    manifest = PilotManifest(
        profile="simulated", operator=args.operator,
        state_dir=args.state_dir, artifact_dir=args.artifact_dir,
        max_steps=args.steps, substrate=args.substrate, seed=args.seed,
        enabled_features={
            "plasticity": args.enable_plasticity_dry_run,
            "plasticity_dry_run": args.enable_plasticity_dry_run,
            "language": args.language, "embodiment": True,
            "sidecar": False, "evaluation": False,
            "local_status_server": False,
        },
        notes="Pilot-0 simulated deployment example")
    # The operator passed these directories explicitly: that is the approval.
    runner = PilotDeploymentRunner(
        manifest=manifest,
        approved_output_roots=[args.state_dir, args.artifact_dir])

    print("risk assessment:")
    for item in runner.assess_risks().items:
        print(f"  [{item.level}] {item.name}: {item.detail}")
    for name in runner.acknowledge_risks(
            note="reviewed in run_pilot_simulated example"):
        print(f"operator {args.operator!r} acknowledged risk: {name}")

    snapshot = runner.run()
    entry = snapshot["registry_entry"] or {}
    readiness = snapshot["readiness"] or {}
    print("=" * 70)
    print("Solaris-AI-NN -- Pilot-0 simulated deployment")
    print("=" * 70)
    print(f"pilot_id:        {manifest.pilot_id}")
    print(f"profile:         {manifest.profile}")
    print(f"readiness:       {'ready' if readiness.get('ready') else 'NOT ready'}")
    print(f"status:          {entry.get('status')}")
    print(f"incidents:       {entry.get('incident_count')}")
    print(f"recommendation:  {entry.get('final_recommendation')}")
    print(f"pilot report:    {entry.get('report_path')}")
    print(f"pilot registry:  {runner.registry.path}")
    if snapshot["refused"]:
        print("refused because:")
        for reason in snapshot["refusal_reasons"]:
            print(f"  - {reason}")


if __name__ == "__main__":
    main()
