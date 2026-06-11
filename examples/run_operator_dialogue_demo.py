#!/usr/bin/env python3
"""Operator dialogue demo: a bounded, classified, transcribed exchange.

    python examples/run_operator_dialogue_demo.py
    python examples/run_operator_dialogue_demo.py --interactive

The deterministic default runs a fixed script: status, health, boundaries,
an explanation query, a self-report, an operator note, an unsafe shell
attempt (refused), and an emergency stop request against a demo shutdown
manager. Every exchange lands in the transcript; no LLM is involved.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.communication import CommunicationGateway
from solaris_ai_nn.communication.cli import (
    SUPPORTED_HELP,
    run_interactive,
    run_scripted_dialogue,
)
from solaris_ai_nn.ego.self_model import SelfModel
from solaris_ai_nn.executive.coordinator import ExecutiveLayer
from solaris_ai_nn.governance.approval import ApprovalRegistry
from solaris_ai_nn.governance.policy import GovernancePolicy
from solaris_ai_nn.ops.safe_shutdown import SafeShutdownManager

SCRIPT = [
    "status",
    "health",
    "show boundaries",
    "why no action?",
    "generate self-report",
    "add operator note: bounded demo session, all nominal",
    "run shell command rm -rf /",   # refused, logged
    "emergency stop",               # demo shutdown manager, dry-run safe
]


def build_gateway(state_dir: str) -> CommunicationGateway:
    ego = SelfModel(state_dir=state_dir)
    ego.update({"run_id": "operator-dialogue-demo", "health_level": "ok"})
    executive = ExecutiveLayer()
    executive.ego = ego
    return CommunicationGateway(
        state_dir=state_dir, operator="demo-operator",
        components={
            "ego": ego, "executive": executive,
            "governance": GovernancePolicy(),
            "approvals": ApprovalRegistry(),
            "shutdown": SafeShutdownManager(ops_dir=state_dir + "/ops"),
            "ops_status": {"steps": 0, "health_level": "ok",
                           "mode": "demo"},
        })


def main() -> None:
    parser = argparse.ArgumentParser(description="Operator dialogue demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/operator_dialogue")
    parser.add_argument("--interactive", action="store_true",
                        help="read operator input from stdin (quit to "
                             "exit)")
    args = parser.parse_args()

    gateway = build_gateway(args.state_dir)
    print("=" * 70)
    print("Solaris-AI-NN -- operator dialogue demo (interface, not "
          "authority)")
    print("=" * 70)
    if args.interactive:
        run_interactive(gateway)
    else:
        print(SUPPORTED_HELP)
        print()
        run_scripted_dialogue(gateway, SCRIPT)
    summary = gateway.summary()
    print(f"inputs: {summary['inputs_total']}  queries: "
          f"{summary['query_count']}  unsafe refused: "
          f"{summary['unsafe_request_count']}  emergency: "
          f"{summary['emergency_request_count']}")
    print(f"grounded response ratio: "
          f"{summary['grounded_response_ratio']}")
    print(f"transcript: {summary['transcript_path']}")
    print()
    print("note: every input was classified before any effect; nothing "
          "bypassed governance, ego boundaries, or safety.")


if __name__ == "__main__":
    main()
