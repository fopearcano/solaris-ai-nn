#!/usr/bin/env python3
"""Architecture review demo: mock evidence -> lifecycle -> review report.

    python examples/run_architecture_review_demo.py --state-dir .solaris_ai_nn_architecture/test_review

Feeds mock research effect evidence into the lifecycle classifier and compiles an
architecture review report. It recommends what to keep, revise, re-test, or
prune -- and never modifies code. Safety-critical modules are blocked from
pruning.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.architecture_evolution import (
    ArchitectureReviewReportBuilder,
    ModuleInventory,
    ModuleLifecycleClassifier,
)


def main():
    parser = argparse.ArgumentParser(description="Architecture review demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_architecture/test_review")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    inv = ModuleInventory()
    clf = ModuleLifecycleClassifier()
    # Mock research effect evidence (provisional, evidence-scoped).
    effects = {"protolanguage": "strong_positive", "world_model": "weak_positive",
               "logos_complexity": "mixed", "latent": "harmful",
               "active_perception": "neutral"}
    evidence = {k: [f"research:{k}"] for k in effects}
    assessments = clf.classify_inventory(inv, effects, evidence)

    report = ArchitectureReviewReportBuilder(
        base_dir=args.state_dir).build_and_write(
        inventory=inv,
        lifecycle_assessments={k: v.to_dict() for k, v in assessments.items()})

    print("=== Architecture review demo ===")
    print(f"lifecycle summary     : {clf.summary(assessments)}")
    print(f"modules to keep       : {report.sections['modules_to_keep'][:6]}...")
    print(f"modules to revise     : {report.sections['modules_to_revise']}")
    print(f"pruning candidates    : "
          f"{report.sections['modules_candidate_for_pruning']}")
    print(f"blocked from pruning  : "
          f"{len(report.sections['modules_blocked_from_pruning'])} "
          "safety-critical")
    print(f"claim-guard safe      : {report.claim_guard_safe}")
    print(f"report                : "
          f"{os.path.join(args.state_dir, 'ARCHITECTURE_REVIEW.md')}")
    print("note                  : recommendations only; no code is modified.")


if __name__ == "__main__":
    main()
