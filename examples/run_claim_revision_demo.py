#!/usr/bin/env python3
"""Claim revision demo: downgrade, add limitation, mark unsupported, block unsafe.

    python examples/run_claim_revision_demo.py --state-dir .solaris_ai_nn_review_assimilation/test_claim_revision

Turns claim impacts into structured revision proposals: a strength downgrade, an
inconclusive mark, an unsupported mark, and a forbidden mark whose unsafe wording
is blocked by ClaimGuard. A proposal never edits the claim registry; safe wording
still includes limitations.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.review_assimilation import (
    ClaimImpactAssessment,
    ClaimImpactType,
    ClaimRevisionProposer,
)


def main():
    parser = argparse.ArgumentParser(description="Claim revision demo")
    parser.add_argument(
        "--state-dir", type=str,
        default=".solaris_ai_nn_review_assimilation/test_claim_revision")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    impacts = [
        ClaimImpactAssessment(claim_id="c1",
                              impact_type=ClaimImpactType.DOWNGRADE_TO_WEAK,
                              rationale="weak evidence under review"),
        ClaimImpactAssessment(claim_id="c1",
                              impact_type=ClaimImpactType.DOWNGRADE_TO_INCONCLUSIVE,
                              rationale="failed reproduction"),
        ClaimImpactAssessment(claim_id="c2",
                              impact_type=ClaimImpactType.MARK_UNSUPPORTED,
                              rationale="no supporting evidence"),
        ClaimImpactAssessment(claim_id="c3",
                              impact_type=ClaimImpactType.MARK_FORBIDDEN,
                              rationale="forbidden inner-state wording"),
    ]
    claim_text = {"c1": "the architecture forms stable signs",
                  "c2": "cross-modal binding emerges",
                  "c3": "the system is conscious"}
    proposals = ClaimRevisionProposer().propose(
        impacts=impacts, claim_text_by_id=claim_text)
    summary = ClaimRevisionProposer.summary(proposals)

    print("=== Claim revision demo ===")
    print(f"  proposals            : {summary['claim_revision_proposal_count']}")
    print(f"  blocked unsafe wording: {summary['blocked_unsafe_wording_count']}")
    for p in summary["proposals"]:
        print(f"    - [{p['status']}] {p['claim_id']}: {p['revision_type']} "
              f"(edits_registry={p['edits_registry']})")
        print(f"        proposed: {p['proposed_wording'][:90]}")
    print("note                 : a revision proposal never edits the claim "
          "registry directly; unsafe wording is blocked by ClaimGuard, and safe "
          "wording still includes limitations.")


if __name__ == "__main__":
    main()
