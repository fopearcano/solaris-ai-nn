#!/usr/bin/env python3
"""Live sign birth gate demo: born, deferred, contaminated, low-utility.

    python examples/run_live_sign_birth_gate_demo.py --state-dir .solaris_ai_nn_live/siggate_demo

Runs the semiogenesis pipeline directly on the safe and contaminated concept
fixtures (with already-trusted concept inputs) and prints the conservative sign birth
gate decision for each candidate: born, deferred, contaminated, or a specific
blocked-by status. The gate is conservative -- it does not enable cognition,
language, or action.
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
    return json.load(open(os.path.join(_FIXTURES, name)))


def main():
    parser = argparse.ArgumentParser(description="Live sign birth gate demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/siggate_demo")
    args = parser.parse_args()

    safe = _load("sample_live_concepts.json")["records"]
    contaminated = _load("sample_contaminated_signs.json")
    concepts = ConceptInputLoader().from_records(
        safe + contaminated["records"], synthetic=True).concepts
    rt = FirstLiveSemiogenesisRuntime(state_dir=args.state_dir,
                                      allow_limited_birth=True)
    rt.analyze_concepts(concepts,
                        requested_tokens=contaminated.get("requested_tokens"))

    print("=== Live sign birth gate demo ===")
    seen = set()
    for g in rt.birth_gate_results:
        status = g["sign_birth_gate_status"]
        seen.add(status)
        print(f"  - {g['sign_id']}: {status} (born={g['born']}) "
              f"-- {g.get('rationale', '')}")
        for b in g.get("blockers", []):
            print(f"      blocker: {b['blocker']} -> {b['correction']}")
    print(f"  distinct gate statuses observed: {sorted(seen)}")
    print("note: the sign birth gate is conservative. It does not enable "
          "cognition, language, or action; it creates only operational private "
          "sign records.")


if __name__ == "__main__":
    main()
