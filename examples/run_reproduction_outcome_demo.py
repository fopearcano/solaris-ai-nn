#!/usr/bin/env python3
"""Reproduction outcome demo: reproduced, not reproduced, blocked, inconclusive.

    python examples/run_reproduction_outcome_demo.py --state-dir .solaris_ai_nn_review_assimilation/test_reproduction_outcome

Ingests four reviewer reproduction outcomes: one reproduced, one not reproduced,
one blocked by a missing artifact (a project limitation), and one inconclusive.
Failed and partial reproduction are evidence; a missing artifact is the project's
limitation, not reviewer failure; and successful reproduction proves nothing about
consciousness/life/agency.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.review_assimilation import ReviewerReproductionOutcomeIngestor


def main():
    parser = argparse.ArgumentParser(description="Reproduction outcome demo")
    parser.add_argument(
        "--state-dir", type=str,
        default=".solaris_ai_nn_review_assimilation/test_reproduction_outcome")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    records = [
        {"challenge_type": "fixture_demo_reproduction", "status": "reproduced",
         "claim_refs": ["c1"]},
        {"challenge_type": "falsification_replay", "status": "not_reproduced",
         "failure_reason": "expected_output_mismatch", "claim_refs": ["c1"]},
        {"challenge_type": "passive_parser_control_comparison",
         "status": "blocked_by_missing_artifact",
         "failure_reason": "missing_fixture", "claim_refs": ["c2"]},
        {"challenge_type": "growth_vs_accumulation_check",
         "status": "inconclusive", "claim_refs": ["c1"]},
    ]
    ingestor = ReviewerReproductionOutcomeIngestor()
    outcomes = ingestor.ingest(records)
    summary = ReviewerReproductionOutcomeIngestor.summary(outcomes)

    print("=== Reproduction outcome demo ===")
    print(f"  outcomes           : {summary['reproduction_outcome_count']}")
    print(f"  success / failure  : {summary['reproduction_success_count']} / "
          f"{summary['reproduction_failure_count']}")
    print(f"  project limitations: {summary['project_limitation_count']}")
    for o in summary["outcomes"]:
        flag = " (project limitation)" if o["is_project_limitation"] else ""
        print(f"    - {o['challenge_type']}: {o['status']}"
              + (f" [{o['failure_reason']}]" if o["failure_reason"] else "")
              + flag + f" (proves_consciousness={o['proves_consciousness']})")
    print("note               : failed/partial reproduction is evidence; a "
          "missing artifact is a project limitation, not reviewer failure; "
          "successful reproduction proves nothing about consciousness/life/"
          "agency.")


if __name__ == "__main__":
    main()
