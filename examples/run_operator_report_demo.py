#!/usr/bin/env python3
"""Operator report demo: ClaimGuard-scanned reports on request.

    python examples/run_operator_report_demo.py

The dialogue requests a status report, a self-report (saved via the ego
layer's scanned builder), and a governance review -- each grounded, each
scanned before anything is written.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.communication import CommunicationGateway
from solaris_ai_nn.ego.self_model import SelfModel
from solaris_ai_nn.governance.compliance import ClaimGuard
from solaris_ai_nn.governance.policy import GovernancePolicy


def main() -> None:
    parser = argparse.ArgumentParser(description="Operator report demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/operator_report")
    args = parser.parse_args()

    Path(args.state_dir).mkdir(parents=True, exist_ok=True)
    ego = SelfModel(state_dir=args.state_dir)
    ego.update({"run_id": "operator-report-demo", "health_level": "ok"})
    gateway = CommunicationGateway(
        state_dir=args.state_dir,
        components={"ego": ego, "governance": GovernancePolicy(),
                    "ops_status": {"health_level": "ok", "steps": 0}})

    print("=" * 70)
    print("Solaris-AI-NN -- operator report demo (scanned before "
          "written)")
    print("=" * 70)
    for text in ("generate status report", "generate self-report",
                 "generate governance review"):
        response = gateway.handle_input(text)
        print(f"> {text}")
        print(f"  [{response.kind}] {response.text[:140]}")
        print()

    report_path = Path(args.state_dir) / "operator_self_report.md"
    if report_path.exists():
        guard = ClaimGuard()
        print(f"self-report on disk: {report_path}")
        print(f"claim guard re-scan of saved Markdown: "
              f"{guard.is_safe(report_path.read_text())}")
    print(f"responses built: {gateway.builder.responses_built}  "
          f"claim guard warnings: "
          f"{gateway.builder.claim_guard_warnings}")
    print()
    print("note: reports are generated through the existing scanned "
          "builders; the gateway adds a transcript row, never new "
          "claims.")


if __name__ == "__main__":
    main()
