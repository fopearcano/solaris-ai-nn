#!/usr/bin/env python3
"""Prompt pack demo: a constrained implementation brief for an external agent.

    python examples/run_prompt_pack_demo.py --state-dir .solaris_ai_nn_experiments/test_prompt_pack

Generates an implementation prompt pack from a compiled spec and shows that the
hard prohibitions, required tests, and docs are included. The prompt never asks
the agent to bypass safety, create a branch, open a PR, or use the network.
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
    PromptPackBuilder,
    compile_spec,
)


def main():
    parser = argparse.ArgumentParser(description="Prompt pack demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_experiments/test_prompt_pack")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    read = ArchitectureProposalReader().read({
        "proposal_id": "p1", "target": "revise_metabolism_thresholds",
        "proposal": "raise the overload threshold",
        "reason": "metabolism prevented overload in replicated runs",
        "evidence_refs": ["replication:replicated", "soak:weekly_review"]})
    spec = compile_spec(read)
    pack = PromptPackBuilder().build(spec.to_dict())
    sections = pack.sections

    out_path = os.path.join(args.state_dir, "IMPLEMENTATION_PROMPT.md")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(pack.render_markdown())

    print("=== Prompt pack demo ===")
    print(f"spec id               : {pack.spec_id}")
    print(f"hard prohibitions     : {len(sections['hard_prohibitions'])}")
    print(f"  includes 'no PR'    : "
          f"{any('pull request' in p for p in sections['hard_prohibitions'])}")
    print(f"  includes 'unrelated': "
          f"{any('unrelated files' in p for p in sections['hard_prohibitions'])}")
    print(f"tests required        : {len(sections['tests'])}")
    print(f"docs updates          : {len(sections['docs_updates'])}")
    print(f"commit message        : {sections['commit_message']}")
    print(f"creates branch        : {pack.to_dict()['creates_branch']}")
    print(f"prompt written        : {out_path}")
    print("note                  : the prompt pack is a constrained brief for a "
          "human-supervised external agent; it never bypasses safety or opens a "
          "PR on its own.")


if __name__ == "__main__":
    main()
