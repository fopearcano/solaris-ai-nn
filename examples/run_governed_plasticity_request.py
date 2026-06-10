#!/usr/bin/env python3
"""Demonstrate that active plasticity requires a human approval record.

    python examples/run_governed_plasticity_request.py

Act 1: an active mutation is attempted without approval -> rejected by
governance (dry-run proposals remain allowed).
Act 2: an approval request is created and a named operator approves it
locally (a deterministic demo of the human step).
Act 3: the same mutation is attempted again -> applied, audited, rollbackable.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.bridges.neural_bridge import SolarisNeuralBridge
from solaris_ai_nn.governance import (
    ApprovalRegistry,
    GovernanceAuditLog,
    GovernancePolicy,
    PermissionScope,
)
from solaris_ai_nn.plasticity.mutation import (
    PlasticityChange,
    PlasticityStep,
    PlasticityTarget,
)
from solaris_ai_nn.plasticity.plasticity_engine import PlasticityEngine


def make_step() -> PlasticityStep:
    return PlasticityStep(
        target=PlasticityTarget("readout", "learning_rate"),
        change=PlasticityChange(old_value=None, new_value=0.05,
                                expected_effect="slightly faster adaptation"),
        reason="demo: tune the readout learning rate",
        trigger_source="experimental")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Active plasticity requires approval (demo)")
    parser.add_argument("--governance-dir", type=str,
                        default=".solaris_ai_nn_governance")
    parser.add_argument("--operator", type=str, default="local-operator")
    args = parser.parse_args()

    audit = GovernanceAuditLog(
        os.path.join(args.governance_dir, "governance_audit.jsonl"))
    approvals = ApprovalRegistry(
        path=os.path.join(args.governance_dir, "approvals.json"), audit=audit)
    policy = GovernancePolicy(approvals=approvals, audit=audit)

    bridge = SolarisNeuralBridge(action_labels=["a", "b"], seed=3)
    engine = PlasticityEngine(bridge=bridge, governance=policy,
                              audit_path=os.path.join(
                                  args.governance_dir,
                                  "demo_plasticity_audit.jsonl"))

    print("=" * 70)
    print("Act 1: active mutation WITHOUT approval")
    print("=" * 70)
    result = engine.apply(make_step())
    print(f"status:  {result.status}")
    print(f"message: {result.message}")
    assert not result.applied, "governance should have rejected this"

    print()
    print("=" * 70)
    print("Act 2: a named human approves the capability")
    print("=" * 70)
    request = approvals.request_approval(
        PermissionScope.ENABLE_PLASTICITY_APPLY,
        reason="demo: allow one bounded plasticity experiment",
        risk_level="high", operator_name=args.operator)
    print(f"request {request.request_id}: {request.requested_permission} "
          f"({request.status})")
    approvals.approve(request.request_id, args.operator,
                      note="reviewed SAFE_BOUNDS; bounded demo only")
    print(f"approved by {args.operator!r}; ledger: {approvals.path}")
    approvals.save()

    print()
    print("=" * 70)
    print("Act 3: the same mutation WITH approval")
    print("=" * 70)
    result = engine.apply(make_step())
    print(f"status:  {result.status}")
    print(f"applied: {result.applied} "
          f"(old={result.old_value} -> new={result.new_value})")
    print(f"rollback available for step {result.step_id}")
    print()
    print(f"governance audit: {audit.path}")
    for row in audit.read_all()[-4:]:
        print(f"  {row['event_type']:22s} {row['decision']:10s} "
              f"{row['reason'][:60]}")


if __name__ == "__main__":
    main()
