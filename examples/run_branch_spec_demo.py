#!/usr/bin/env python3
"""Branch spec demo: a PR-ready draft with no Git operation performed.

    python examples/run_branch_spec_demo.py --state-dir .solaris_ai_nn_experiments/test_branch_spec

Generates a PR-ready branch spec (suggested branch name, draft PR title/body,
review checklist, merge blockers) from a compiled spec. No Git branch is created
and no pull request is opened.
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
    BranchSpecBuilder,
    compile_spec,
)


def main():
    parser = argparse.ArgumentParser(description="Branch spec demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_experiments/test_branch_spec")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    read = ArchitectureProposalReader().read({
        "proposal_id": "p1", "target": "revise_semiogenesis_thresholds",
        "proposal": "lower the sign-stability threshold",
        "reason": "useful signs replicated under non-human sensorium",
        "evidence_refs": ["replication:sign_utility_improved"]})
    spec = compile_spec(read)
    branch = BranchSpecBuilder().build(spec.to_dict())

    out_path = os.path.join(args.state_dir, "BRANCH_SPEC.md")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(branch.render_markdown())

    print("=== Branch spec demo ===")
    print(f"suggested branch name : {branch.suggested_branch_name} "
          "(NOT created)")
    print(f"PR title (draft)      : {branch.pr_title_suggestion}")
    print(f"review checklist items: {len(branch.review_checklist)}")
    print(f"merge blockers        : {len(branch.merge_blockers)}")
    print(f"branch created        : {branch.to_dict()['branch_created']}")
    print(f"PR opened             : {branch.to_dict()['pr_opened']}")
    print(f"branch spec written   : {out_path}")
    print("note                  : the branch name and PR title/body are drafts "
          "only. No Git branch was created and no pull request was opened.")


if __name__ == "__main__":
    main()
