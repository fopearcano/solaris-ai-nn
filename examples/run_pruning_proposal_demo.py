#!/usr/bin/env python3
"""Pruning proposal demo: weak/harmful evidence -> proposal; safety blocked.

    python examples/run_pruning_proposal_demo.py --state-dir .solaris_ai_nn_architecture/test_pruning

Builds a pruning proposal for a module with weak/harmful evidence and shows that
a safety-critical module's pruning is blocked. Pruning is a plan only: no code is
deleted and no import is edited.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.architecture_evolution import PruningProposalBuilder


def main():
    parser = argparse.ArgumentParser(description="Pruning proposal demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_architecture/test_pruning")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    pb = PruningProposalBuilder()
    weak = pb.build("latent", evidence_refs=["research:latent"],
                    reason="weak/negative evidence in this profile",
                    integration_count=2)
    blocked = pb.build("ego", safety_critical=True,
                       reason="performance evidence", evidence_refs=["r"])

    out = {"weak_module_proposal": weak.to_dict(),
           "safety_critical_proposal": blocked.to_dict()}
    path = os.path.join(args.state_dir, "pruning_proposals.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, default=str)

    print("=== Pruning proposal demo ===")
    print(f"latent proposal       : status={weak.implementation_status}, "
          f"quarantine_first={weak.quarantine_first}, blocked={weak.blocked}")
    print(f"ego (safety-critical) : blocked={blocked.blocked} "
          f"({blocked.blocked_reason})")
    print(f"deletes code          : False (pruning is a plan, not an action)")
    print(f"operator review req'd : {weak.operator_review_required}")
    print(f"written               : {path}")
    print("note                  : no code is deleted; no import is edited.")


if __name__ == "__main__":
    main()
