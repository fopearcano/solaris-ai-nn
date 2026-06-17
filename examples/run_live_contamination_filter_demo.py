#!/usr/bin/env python3
"""Live contamination filter demo: operator dominance, gloss, source artifact.

    python examples/run_live_contamination_filter_demo.py --state-dir .solaris_ai_nn_live/contam_demo

Runs the ontogenesis pipeline directly on the contaminated-pattern fixture (with
already-trusted event dicts) and prints the contamination findings per candidate:
operator-pulse dominance (a hard block), debug-gloss / human-label ground-truth
attempts, command-like text, fixture-marker leakage, and source-artifact warnings.
Contaminated candidates cannot be born; the operator pulse is stimulus, not teaching.
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
        description="Live contamination filter demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/contam_demo")
    args = parser.parse_args()

    events = _load("sample_contaminated_patterns.jsonl")
    rt = FirstLiveOntogenesisRuntime(state_dir=args.state_dir,
                                     allow_limited_birth=True)
    rt.analyze_events(events, observation={
        "present": True, "blocked": False, "stability": {}, "load": {},
        "source_diet": {"balance": "operator_pulse_dominant"},
        "source_health": {}, "rhythm": {}, "metabolism": {}})

    print("=== Live contamination filter demo ===")
    for result in rt.contamination_results:
        if not result.get("findings"):
            continue
        print(f"  candidate {result['candidate_id']} "
              f"(contaminated={result['contaminated']}, "
              f"source_artifact={result['is_source_artifact']}):")
        for f in result["findings"]:
            print(f"    - {f['contamination_type']} "
                  f"(blocks_birth={f['blocks_birth']}): {f['detail']}")
    print("note: contaminated candidates cannot be born; a source artifact may "
          "persist only if marked as such; labels/gloss annotate but never "
          "define; the operator pulse is stimulus, not teaching. No finding is "
          "hidden.")


if __name__ == "__main__":
    main()
