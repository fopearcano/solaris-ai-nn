#!/usr/bin/env python3
"""Experiment compiler demo: proposal -> spec -> prompt pack -> branch spec.

    python examples/run_experiment_compiler_demo.py --state-dir .solaris_ai_nn_experiments/test_compiler

Compiles a synthetic architecture proposal into a compiled experiment spec, an
implementation prompt pack, a PR-ready branch spec, and a report. The compiler
writes documents only: no source change, no Git branch, no PR, no external agent.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.experiment_compiler import ExperimentCompilerRuntime


def main():
    parser = argparse.ArgumentParser(description="Experiment compiler demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_experiments/test_compiler")
    args = parser.parse_args()

    rt = ExperimentCompilerRuntime(state_dir=args.state_dir, max_specs=10)
    rt.load_manifest(proposals=[
        {"proposal_id": "p1", "target": "revise_sensorium_profiles",
         "proposal": "broaden the source diet to reduce fixture overfit",
         "reason": "replication flagged fixture overfit",
         "evidence_refs": ["replication:fixture_overfit",
                           "soak:POST_RUN_AUTOPSY"]},
        {"proposal_id": "p2", "target": "promote_stable_modules",
         "proposal": "promote a module whose structure replicated",
         "reason": "structure replicated across runs",
         "evidence_refs": ["replication:replicated"]}],
        operator_note="prioritize the sensorium diet change")
    rt.compile()
    out = rt.write_artifacts()
    st = rt.compiler_status()

    print("=== Experiment compiler demo ===")
    print(f"compiled specs        : {st['compiled_spec_count']} "
          f"(ready {st['ready_spec_count']}, blocked {st['blocked_spec_count']})")
    print(f"prompt packs          : {st['prompt_pack_count']}")
    print(f"branch specs          : {st['branch_spec_count']}")
    print(f"safety gate failures  : {st['safety_gate_failure_count']}")
    print(f"modifies source       : {st['modifies_source']}")
    print(f"creates branch        : {st['creates_branch']}")
    print(f"report                : {out['markdown']}")
    print(f"per-experiment docs   : {len(out['per_experiment'])}")
    print("note                  : the compiler writes documents only; it "
          "changes no source, creates no Git branch, opens no pull request, "
          "and runs no external coding agent.")


if __name__ == "__main__":
    main()
