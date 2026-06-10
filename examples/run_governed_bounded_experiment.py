#!/usr/bin/env python3
"""Run a bounded experiment through the full governance layer.

    python examples/run_governed_bounded_experiment.py --steps 100
    python examples/run_governed_bounded_experiment.py --embodied --language
    python examples/run_governed_bounded_experiment.py --enable-plasticity-dry-run

The default configuration is bounded, simulation-only, and needs no approval.
Medium risks (e.g. embodiment) are shown to the operator and acknowledged
explicitly here -- this script is the operator acting, not a bypass.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.governance import (
    OperatorProfile,
    OperatorSession,
    assess_manifest,
)
from solaris_ai_nn.ops import OperationalRunManifest, OperationalSupervisor


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Governed bounded experiment (safe defaults)")
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/governed_demo")
    parser.add_argument("--artifact-dir", type=str, default=".solaris_ai_nn_ops")
    parser.add_argument("--governance-dir", type=str,
                        default=".solaris_ai_nn_governance")
    parser.add_argument("--operator", type=str, default="local-operator")
    parser.add_argument("--embodied", action="store_true")
    parser.add_argument("--language", action="store_true")
    parser.add_argument("--enable-plasticity-dry-run", action="store_true",
                        help="propose-only plasticity (allowed by default)")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    manifest = OperationalRunManifest(
        mode="bounded", max_steps=args.steps,
        state_dir=args.state_dir, artifact_dir=args.artifact_dir,
        seed=args.seed,
        healthcheck_interval_steps=max(25, args.steps // 4),
        enabled_features={
            "plasticity": args.enable_plasticity_dry_run,
            "plasticity_dry_run": args.enable_plasticity_dry_run,
            "embodiment": args.embodied,
            "language": args.language,
            "sidecar": False, "evaluation": False,
            "local_status_server": False,
        },
        operator_notes="governed bounded experiment example")

    # The operator reviews the risk assessment and acknowledges medium risks.
    session = OperatorSession(
        operator=OperatorProfile(name=args.operator, role="researcher"))
    risk = assess_manifest(manifest)
    print("risk assessment:")
    for item in risk.items:
        print(f"  [{item.level}] {item.name}: {item.detail}")
    for item in risk.acknowledgeable_items():
        session.acknowledge_risk(item.name,
                                 note="reviewed in run_governed_bounded_"
                                      "experiment example")
        print(f"operator {args.operator!r} acknowledged risk: {item.name}")

    supervisor = OperationalSupervisor(
        manifest=manifest, operator_session=session,
        governance_dir=args.governance_dir)
    status = supervisor.run()
    governance = status.get("governance") or {}

    print("=" * 70)
    print("Solaris-AI-NN -- governed bounded experiment")
    print("=" * 70)
    print(f"run_id:           {manifest.run_id}")
    print(f"policy status:    {governance.get('policy_status')}")
    print(f"risk level:       {governance.get('risk_level')}")
    print(f"health:           {(status['health'] or {}).get('level', 'unknown')}")
    print(f"lifetime steps:   {(status['telemetry'] or {}).get('lifetime_steps')}")
    print(f"incidents:        {status['incident_count']}")
    print(f"claim guard:      {governance.get('claim_guard_status')}")
    print(f"recommendation:   "
          f"{governance.get('post_run_review_recommendation')}")
    print(f"governance audit: {governance.get('governance_audit_path')}")
    print(f"final status:     {supervisor.ops_dir}/status.md")
    if governance.get("refusal_reasons"):
        print("refused because:")
        for reason in governance["refusal_reasons"]:
            print(f"  - {reason}")


if __name__ == "__main__":
    main()
