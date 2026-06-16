#!/usr/bin/env python3
"""Independent review demo: manifest, reviewer pack, readiness report.

    python examples/run_independent_review_demo.py --state-dir .solaris_ai_nn_review/test_review

Prepares a local, offline independent review package from a clean evidence set:
indexes artifacts, scans for leak/forbidden risks, builds the reviewer pack,
reproducibility challenges, audit matrix, and review readiness report. It
publishes nothing, uploads nothing, contacts no reviewer, calls no Git/GitHub, and
executes no command or experiment.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.independent_review import IndependentReviewRuntime


def main():
    parser = argparse.ArgumentParser(description="Independent review demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_review/test_review")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    bundle = {
        "research_baseline": {"baseline_status": "validated",
                              "safety_boundary_status": "pass"},
        "research_cycle": {"current_cycle_stage": "research_baseline_validated"},
        "replication": {"replication_arm_count": 3},
        "falsification": {"falsified_claim_count": 0},
        "soak": {"log_accumulation_warning": False},
        "safety": {"critical_regression_count": 0},
        "scientific_claims": {
            "claim_registry": {"scientific_claim_count": 2,
                               "supported_claim_count": 1, "claims": [
                {"claim_id": "c1",
                 "text": "Signs form under bounded fixtures.",
                 "category": "sensorium_claim", "status": "supported",
                 "evidence_refs": ["e1"], "counterevidence_refs": []},
                {"claim_id": "c2", "text": "Binding emerges everywhere.",
                 "category": "sensorium_claim", "status": "unsupported",
                 "evidence_refs": [], "counterevidence_refs": []}]},
            "counterevidence": {"counterevidence_count": 0, "records": []},
            "forbidden_claims": {"asserted_forbidden_count": 0,
                                 "blocks_publication": False},
            "limitations": {"limitation_count": 4, "limitations": [
                {"category": "no_consciousness_evidence",
                 "text": "No evidence of consciousness exists or is claimed."}]}},
        "sanitizer_inputs": {
            "abstract": "Operational signs form under bounded fixtures. It is "
                        "not conscious and makes no claim of agency."},
    }
    rt = IndependentReviewRuntime(state_dir=args.state_dir)
    rt.load_bundle(bundle)
    rt.run()
    rt.write_artifacts()
    st = rt.independent_review_status()

    print("=== Independent review demo ===")
    print(f"  artifacts indexed     : {st['independent_review_artifact_count']} "
          f"(missing {st['missing_review_artifact_count']})")
    print(f"  sanitizer findings    : {st['sanitizer_finding_count']} "
          f"({st['critical_sanitizer_finding_count']} critical)")
    print(f"  repro challenges      : {st['reproducibility_challenge_count']} "
          f"(unavailable {st['unavailable_challenge_count']})")
    print(f"  reviewer questions    : {st['reviewer_question_count']}")
    print(f"  adversarial alts      : {st['alternative_explanation_count']}")
    print(f"  audit matrix blockers : {st['audit_matrix_blocker_count']}")
    print(f"  review readiness      : {st['review_readiness_status']}")
    print(f"  published / uploaded  : {st['published']} / {st['uploaded']}")
    print(f"  report                : "
          f"{st['latest_independent_review_report_path']}")
    print("note                    : the independent review layer prepares a "
          "local offline review package. It publishes nothing, uploads nothing, "
          "contacts no reviewer, calls no Git/GitHub, executes no command, and "
          "makes no consciousness/life/agency claim.")


if __name__ == "__main__":
    main()
