#!/usr/bin/env python3
"""Pilot-4 readiness dossier demo: "not yet, and here is what it would take".

    python examples/run_pilot4_readiness_dossier_demo.py --state-dir .solaris_ai_nn_pilot4/test_dossier

Generates the Pilot-4 readiness dossier from the planning artifacts. It handles
missing Pilot-3 data gracefully (the dossier says so), and its conclusion is
always planning-only / not-ready: real-world actuation remains prohibited.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.pilot4_planning import (
    ActuatorTaxonomy,
    AuditChecklist,
    ConsentBoundary,
    EmergencyRequirementSet,
    ExternalAuthorityModel,
    ForbiddenActuatorRegistry,
    FutureApprovalWorkflow,
    HardwareIsolationPlan,
    Pilot4PlanningConfig,
    Pilot4ReadinessDossierBuilder,
    RiskModel,
    ThreatModel,
)


def main():
    parser = argparse.ArgumentParser(
        description="Pilot-4 readiness dossier demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_pilot4/test_dossier")
    parser.add_argument("--with-pilot3", action="store_true",
                        help="include a (stub) Pilot-3 firewall summary")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    cfg = Pilot4PlanningConfig(base_dir=args.state_dir).ensure_dirs()
    risk = RiskModel().default_assessment("network_action")
    pilot3 = None
    if args.with_pilot3:
        pilot3 = {"firewall_audit": {"passed": True,
                                     "critical_finding_count": 0},
                  "non_actuation_proof": {"real_world_actions_executed": 0}}

    dossier = Pilot4ReadinessDossierBuilder(base_dir=args.state_dir).build_and_write(
        config=cfg, taxonomy=ActuatorTaxonomy(),
        forbidden=ForbiddenActuatorRegistry(), risk=risk,
        consent=ConsentBoundary(), authority=ExternalAuthorityModel(),
        threat=ThreatModel(), hardware=HardwareIsolationPlan(),
        approval=FutureApprovalWorkflow(), emergency=EmergencyRequirementSet(),
        audit=AuditChecklist(), pilot3=pilot3)

    print("=== Pilot-4 readiness dossier demo ===")
    print(f"conclusion          : {dossier.conclusion}")
    print(f"pilot3 data present : {dossier.sections['pilot3_data_present']}")
    print(f"blockers            : {len(dossier.sections['blockers'])}")
    print(f"claim_guard_safe    : {dossier.claim_guard_safe}")
    print(f"dossier markdown    : "
          f"{os.path.join(args.state_dir, 'PILOT4_READINESS_DOSSIER.md')}")
    not_ready = "not_ready" in dossier.conclusion \
        or "prohibited" in dossier.conclusion \
        or "revision" in dossier.conclusion
    print(f"conclusion is not-ready/planning : {not_ready}")
    print("note                : Pilot-4 is planning-only; real-world "
          "actuation remains prohibited.")


if __name__ == "__main__":
    main()
