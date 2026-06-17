#!/usr/bin/env python3
"""Live sign utility demo: useful sign, low-utility sign, label-dependent.

    python examples/run_live_sign_utility_demo.py --state-dir .solaris_ai_nn_live/sigutil_demo

Runs the semiogenesis pipeline directly on the safe and contaminated concept
fixtures (with already-trusted concept inputs) and prints each sign candidate's
utility score and verdict. A sign must do something internally useful; merely naming
a concept is not enough; a label-mirroring sign has low or blocked utility.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.live_semiogenesis import (
    ConceptInputLoader,
    FirstLiveSemiogenesisRuntime,
)

_FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "live_semiogenesis")


def _load(name):
    return json.load(open(os.path.join(_FIXTURES, name)))["records"]


def main():
    parser = argparse.ArgumentParser(description="Live sign utility demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/sigutil_demo")
    args = parser.parse_args()

    concepts = ConceptInputLoader().from_records(
        _load("sample_live_concepts.json") + _load("sample_contaminated_signs.json"),
        synthetic=True).concepts
    cdata = json.load(open(os.path.join(_FIXTURES,
                                        "sample_contaminated_signs.json")))
    rt = FirstLiveSemiogenesisRuntime(state_dir=args.state_dir,
                                      allow_limited_birth=True)
    rt.analyze_concepts(concepts, requested_tokens=cdata.get("requested_tokens"))

    print("=== Live sign utility demo ===")
    for cand in sorted(rt.candidates, key=lambda c: -c.utility_score):
        score = rt.utility_scores.get(cand.sign_id, {})
        print(f"  - {cand.sign_id}: utility={cand.utility_score:.2f} "
              f"useful={score.get('useful')} status={cand.status} "
              f"contam={cand.contamination_findings or 'none'}")
        for note in score.get("notes", []):
            print(f"      note: {note}")
    print("note: a sign must be internally useful; merely naming a concept is "
          "not enough; a label-mirroring sign has low or blocked utility; "
          "missing evidence lowers confidence.")


if __name__ == "__main__":
    main()
