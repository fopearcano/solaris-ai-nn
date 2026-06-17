#!/usr/bin/env python3
"""Live proto-concept candidate demo: emerging, stable, rejected, contaminated.

    python examples/run_live_proto_concept_candidate_demo.py --state-dir .solaris_ai_nn_live/cand_demo

Runs the ontogenesis analysis pipeline directly on the stable, inconclusive, and
contaminated fixtures (bypassing the inbox/observation gating, with already-trusted
event dicts) so it can show the full range of candidate statuses: emerging /
stabilizing / stable candidate / born, weak, suspended, rejected, contaminated, and
source-artifact. A candidate is not a concept until it passes the birth gate.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.live_ontogenesis import FirstLiveOntogenesisRuntime

_FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "live_ontogenesis")


def _load(fixture: str):
    path = os.path.join(_FIXTURES, fixture)
    rows = []
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    return rows


def main():
    parser = argparse.ArgumentParser(
        description="Live proto-concept candidate demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/cand_demo")
    args = parser.parse_args()

    events = (_load("sample_stable_patterns.jsonl")
              + _load("sample_inconclusive_patterns.jsonl")
              + _load("sample_contaminated_patterns.jsonl"))
    rt = FirstLiveOntogenesisRuntime(state_dir=args.state_dir,
                                     allow_limited_birth=True)
    rt.analyze_events(events)

    print("=== Live proto-concept candidate demo ===")
    print(f"  events    : {len(events)}")
    print(f"  candidates: {len(rt.candidates)}")
    for c in sorted(rt.candidates, key=lambda x: -x.stability_score):
        print(f"    - [{c.status:16}] recurrence={c.recurrence_count:<3} "
              f"stability={c.stability_score:.2f} "
              f"support={c.supporting_count} counter={c.counter_count} "
              f"sources={list(c.source_distribution)}")
    print("note      : a candidate is not a concept until it passes the birth "
          "gate. Weak, rejected, suspended, and contaminated candidates remain "
          "visible; supporting and contradicting evidence are preserved.")


if __name__ == "__main__":
    main()
