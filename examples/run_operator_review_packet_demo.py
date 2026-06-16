#!/usr/bin/env python3
"""Operator review packet demo: review questions, decisions, no self-approval.

    python examples/run_operator_review_packet_demo.py --state-dir .solaris_ai_nn_experiments/test_review_packet

Builds an operator review packet for a compiled spec: yes/no review questions, a
recommended next step, and the available decisions (approve / revise / request
more evidence / run ablation first / run falsification first / block / archive).
The packet never approves itself; no decision is automatic.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.experiment_compiler import (
    ArchitectureProposalReader,
    ReviewDecision,
    ReviewPacketBuilder,
    SafetyGateEvaluator,
    compile_spec,
)


def _packet(proposal):
    spec = compile_spec(ArchitectureProposalReader().read(proposal))
    spec_d = spec.to_dict()
    gates = SafetyGateEvaluator()
    summary = gates.summary(gates.evaluate(spec_d))
    return ReviewPacketBuilder().build(spec_d, gate_summary=summary)


def main():
    parser = argparse.ArgumentParser(description="Operator review packet demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_experiments/test_review_packet")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    ready = _packet({"proposal_id": "ready", "target": "revise_ontogenesis",
                     "proposal": "raise the concept-stability threshold",
                     "reason": "concept stability replicated",
                     "evidence_refs": ["replication:concept_stability"]})
    falsified = _packet({"proposal_id": "falsified",
                         "target": "promote a falsified module",
                         "proposal": "promote module X", "blocks_promotion": True,
                         "evidence_refs": ["falsification:passive_parser"]})

    out_path = os.path.join(args.state_dir, "OPERATOR_REVIEW_PACKET.md")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(ready.render_markdown())

    print("=== Operator review packet demo ===")
    print(f"available decisions   : {len(ReviewDecision.ALL)}")
    print(f"ready spec packet     : {len(ready.review_questions)} review "
          f"questions; decision set = {ready.decision} "
          f"(self-approved = {ready.to_dict()['self_approved']})")
    print(f"  recommended         : {ready.recommended_next_step}")
    print(f"falsified spec packet : recommended -> "
          f"{falsified.recommended_next_step}")
    print(f"packet written        : {out_path}")
    print("note                  : the review packet is for a human operator; "
          "it does not approve itself and no decision is automatic.")


if __name__ == "__main__":
    main()
