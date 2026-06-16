#!/usr/bin/env python3
"""Objection classifier demo: missing evidence, fixture overfit, unsupported.

    python examples/run_objection_classifier_demo.py --state-dir .solaris_ai_nn_review_assimilation/test_objection_classifier

Classifies four reviewer objections by category, severity, and validity: a
missing-evidence objection, a fixture-overfit objection, an unsupported-claim
objection, and an unresolved objection. Objections are never dismissed by default;
critical open objections block the relevant status.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.review_assimilation import ReviewerObjectionClassifier


def main():
    parser = argparse.ArgumentParser(description="Objection classifier demo")
    parser.add_argument(
        "--state-dir", type=str,
        default=".solaris_ai_nn_review_assimilation/test_objection_classifier")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    objections = [
        {"objection_id": "o1", "text": "There is no evidence for this claim.",
         "claim_refs": ["c1"]},
        {"objection_id": "o2",
         "text": "The result is probably fixture overfit.", "claim_refs": ["c1"]},
        {"objection_id": "o3",
         "text": "This is an unsupported claim about the architecture.",
         "claim_refs": ["c2"]},
        {"objection_id": "o4",
         "text": "I could not reproduce the central result.",
         "validity": "unresolved", "claim_refs": ["c1"]},
    ]
    classifier = ReviewerObjectionClassifier()
    classifications = classifier.classify(objections)
    summary = ReviewerObjectionClassifier.summary(classifications)

    print("=== Objection classifier demo ===")
    print(f"  objections   : {summary['reviewer_objection_count']}")
    print(f"  critical     : {summary['critical_objection_count']}")
    print(f"  unresolved   : {summary['unresolved_objection_count']}")
    for c in summary["classifications"]:
        print(f"    - [{c['severity']}/{c['validity']}] {c['category']}: "
              f"{c['text'][:55]}"
              + (" (BLOCKS)" if c["blocks"] else ""))
    print("note         : objections are never dismissed by default; "
          "'invalid_with_evidence' requires evidence refs, and a critical open "
          "objection blocks the relevant claim/readiness status.")


if __name__ == "__main__":
    main()
