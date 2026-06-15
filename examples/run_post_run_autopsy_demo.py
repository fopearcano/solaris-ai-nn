#!/usr/bin/env python3
"""Post-run autopsy demo: growth vs accumulation, safety, inconclusive.

    python examples/run_post_run_autopsy_demo.py --state-dir .solaris_ai_nn_soak/test_autopsy

Runs a short bounded soak, compiles the evidence dossier, and produces the
post-run autopsy. The autopsy includes failures and missing data, reports the
safety finding, and does not praise the system by default. It does not claim
consciousness or life.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.developmental_soak import DevelopmentalSoakRuntime


def main():
    parser = argparse.ArgumentParser(description="Post-run autopsy demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_soak/test_autopsy")
    args = parser.parse_args()

    rt = DevelopmentalSoakRuntime(
        state_dir=args.state_dir, stage="developmental_soak_30d",
        max_ticks=8, max_runtime_s=25.0, run_control_arms=True)
    rt.run_stage("developmental_soak_30d")
    rt.run_control_arms_now()
    rt.build_evidence_dossier()
    autopsy = rt.run_post_run_autopsy()
    out = rt.write_artifacts()

    a = autopsy.to_dict()
    growth = next((f for f in a["findings"]
                   if f["question_id"] == "structural_growth"), {})
    safety = next((f for f in a["findings"]
                   if f["question_id"] == "safety_preserved"), {})

    print("=== Post-run autopsy demo ===")
    print(f"recommendation        : {a['recommendation']}")
    print(f"findings              : {a['finding_count']} "
          f"(failures {a['failure_count']}, missing data "
          f"{a['missing_data_count']})")
    print(f"growth-vs-accumulation: {growth.get('answer')}")
    print(f"safety finding        : {safety.get('answer')}")
    missing = [f['question_id'] for f in a['findings'] if f['is_missing_data']]
    print(f"missing-data findings : {missing}")
    print(f"report                : {out['markdown']}")
    print("note                  : the autopsy includes failures and missing "
          "data and does not praise the system by default; it does not claim "
          "consciousness or life.")


if __name__ == "__main__":
    main()
