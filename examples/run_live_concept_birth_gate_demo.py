#!/usr/bin/env python3
"""Live concept birth gate demo: born, deferred, contaminated, inconclusive.

    python examples/run_live_concept_birth_gate_demo.py --state-dir .solaris_ai_nn_live/gate_demo

Runs the ontogenesis pipeline directly on the stable, inconclusive, and contaminated
fixtures (with already-trusted event dicts) and prints the conservative concept birth
gate decision for each candidate: born, stable candidate, defer, contaminated, or a
specific blocked-by status. The gate is conservative -- it does not enable
semiogenesis, create language, or claim understanding.
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
        description="Live concept birth gate demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/gate_demo")
    args = parser.parse_args()

    events = (_load("sample_stable_patterns.jsonl")
              + _load("sample_inconclusive_patterns.jsonl")
              + _load("sample_contaminated_patterns.jsonl"))
    rt = FirstLiveOntogenesisRuntime(state_dir=args.state_dir,
                                     allow_limited_birth=True)
    rt.analyze_events(events)

    print("=== Live concept birth gate demo ===")
    seen = set()
    for g in rt.birth_gate_results:
        status = g["concept_birth_gate_status"]
        # Show one representative example of each distinct status.
        line = (f"  - {g['candidate_id']}: {status} (born={g['born']}) "
                f"-- {g.get('rationale', '')}")
        print(line)
        seen.add(status)
        for b in g.get("blockers", []):
            print(f"      blocker: {b['blocker']} -> {b['correction']}")
    print(f"  distinct gate statuses observed: {sorted(seen)}")
    print("note: the birth gate is conservative. It does not enable "
          "semiogenesis, create language, or claim understanding; it creates "
          "only operational proto-concept records.")


if __name__ == "__main__":
    main()
