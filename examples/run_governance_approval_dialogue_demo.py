#!/usr/bin/env python3
"""Governance approval dialogue demo: decisions onto real requests only.

    python examples/run_governance_approval_dialogue_demo.py

A pending approval is created, listed, approved through the dialogue;
a second is rejected; an unknown id and an expired request are both
refused with grounded explanations.
"""

from __future__ import annotations

import argparse
import os
import sys
import time

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.communication import CommunicationGateway
from solaris_ai_nn.governance.approval import ApprovalRegistry
from solaris_ai_nn.governance.policy import GovernancePolicy


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Governance approval dialogue demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/approval_dialogue")
    args = parser.parse_args()

    registry = ApprovalRegistry()
    to_approve = registry.request_approval(
        "enable_sidecar_suggestions", reason="demo: publish suggestions")
    to_reject = registry.request_approval(
        "enable_plasticity_apply", reason="demo: live plasticity")
    expired = registry.request_approval(
        "run_soak_24h", reason="demo: soak", expires_in_s=0.05)
    time.sleep(0.1)

    gateway = CommunicationGateway(
        state_dir=args.state_dir, operator="demo-operator",
        components={"approvals": registry,
                    "governance": GovernancePolicy()})

    print("=" * 70)
    print("Solaris-AI-NN -- governance approval dialogue demo")
    print("=" * 70)
    script = [
        "what approvals are pending?",
        f"approve request {to_approve.request_id}",
        f"reject request {to_reject.request_id}",
        f"approve request {expired.request_id}",   # expired: refused
        "approve request nonexistent00",           # unknown: refused
    ]
    for text in script:
        response = gateway.handle_input(text)
        print(f"> {text}")
        print(f"  [{response.kind}] {response.text[:130]}")
        print()
    print(f"final statuses: {to_approve.request_id}="
          f"{registry.requests[to_approve.request_id].status}  "
          f"{to_reject.request_id}="
          f"{registry.requests[to_reject.request_id].status}  "
          f"{expired.request_id}="
          f"{registry.requests[expired.request_id].status}")
    print(f"approvals processed: "
          f"{gateway.approval_router.approvals_processed}  rejections: "
          f"{gateway.approval_router.rejections_processed}  refused: "
          f"{gateway.approval_router.refused}")
    print()
    print("note: approvals act only on real pending requests, expire on "
          "schedule, and bypass nothing prohibited.")


if __name__ == "__main__":
    main()
