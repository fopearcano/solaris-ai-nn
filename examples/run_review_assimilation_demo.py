#!/usr/bin/env python3
"""Review assimilation demo: objection, claim impact, experiment, report.

    python examples/run_review_assimilation_demo.py --state-dir .solaris_ai_nn_review_assimilation/test_assimilation

Assimilates local reviewer feedback (a fixture-overfit objection, a failed
reproduction, and a forbidden-claim-risk objection) into the research ledger:
classifies objections, assesses claim impact, recommends experiments, revises
publication readiness, and writes the report set. Reviewer feedback is research
evidence -- not model training; nothing is published, uploaded, or contacted.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.review_assimilation import ReviewerFeedbackAssimilationRuntime


def main():
    parser = argparse.ArgumentParser(description="Review assimilation demo")
    parser.add_argument(
        "--state-dir", type=str,
        default=".solaris_ai_nn_review_assimilation/test_assimilation")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    bundle = {
        "independent_review": {
            "response_ledger": {"objections": [
                {"objection_id": "o_led", "text": "No live-field replication.",
                 "status": "unresolved", "claim_refs": ["c1"]}]},
            "adversarial_findings": {"explanations": [
                {"explanation_type": "fixture_overfit", "strong": True}]},
            "audit_matrix": {"audit_matrix_blocker_count": 1},
            "review_readiness": {
                "review_readiness_status": "ready_for_internal_review"}},
        "scientific_claims": {
            "claim_registry": {"claims": [
                {"claim_id": "c1", "text": "Signs form under bounded fixtures.",
                 "status": "supported"},
                {"claim_id": "c2", "text": "Binding emerges everywhere.",
                 "status": "weakly_supported"}]},
            "forbidden_claims": {"asserted_forbidden_count": 0},
            "limitations": {"limitation_count": 4}},
        "objections": [
            {"objection_id": "o1", "text": "Could this be fixture overfit?",
             "claim_refs": ["c1"]},
            {"objection_id": "o2",
             "text": "This wording risks a forbidden consciousness claim.",
             "severity": "critical", "claim_refs": ["c2"]}],
        "reproduction_outcomes": [
            {"challenge_type": "fixture_demo_reproduction",
             "status": "reproduced", "claim_refs": ["c1"]},
            {"challenge_type": "falsification_replay", "status": "not_reproduced",
             "failure_reason": "missing_fixture", "claim_refs": ["c1"]}],
        "missing_artifacts": ["soak_dossier"],
    }
    rt = ReviewerFeedbackAssimilationRuntime(state_dir=args.state_dir)
    rt.load_bundle(bundle)
    rt.run()
    rt.write_artifacts()
    st = rt.review_assimilation_status()

    print("=== Review assimilation demo ===")
    print(f"  feedback artifacts    : {st['reviewer_feedback_artifact_count']}")
    print(f"  objections            : {st['reviewer_objection_count']} "
          f"(critical {st['critical_objection_count']}, unresolved-critical "
          f"{st['unresolved_critical_objection_count']})")
    print(f"  reproduction failures : {st['reproduction_failure_count']}")
    print(f"  claim downgrades      : {st['claim_downgrade_count']}")
    print(f"  evidence gaps         : {st['evidence_gap_count']}")
    print(f"  experiment recs       : {st['reviewer_driven_experiment_count']}")
    print(f"  claim revisions       : {st['claim_revision_proposal_count']}")
    print(f"  publication readiness : {st['publication_readiness_impact']}")
    print(f"  trains model          : {st['trains_model']}")
    print(f"  published / contacted : {st['published']} / "
          f"{st['contacted_reviewers']}")
    print(f"  report                : "
          f"{st['latest_review_assimilation_report_path']}")
    print("note                    : reviewer feedback is assimilated as research "
          "evidence, not model training. Nothing was published, uploaded, or "
          "contacted, and no consciousness/life/agency claim is made.")


if __name__ == "__main__":
    main()
