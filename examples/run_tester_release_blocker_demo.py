#!/usr/bin/env python3
"""Tester release blocker demo: missing membrane, claim, fixture; waived non-critical.

    python examples/run_tester_release_blocker_demo.py \\
        --tester-state-dir .solaris_ai_nn_tester/test_release_blocker

Builds a release blocker gate with a missing-membrane blocker, an unsupported-claim
blocker, and a fixture-demo blocker, then shows that a non-critical blocker can be waived
with a reason while a critical safety blocker cannot be silently waived.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_safety_freeze import (
    ReleaseBlockerCategory,
    TesterReleaseBlockerGate,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/test_release_blocker")
    ap.parse_args()

    gate = TesterReleaseBlockerGate()
    membrane = gate.add(ReleaseBlockerCategory.MISSING_MEMBRANE,
                        "live modules ran but no membrane report present")
    claim = gate.add(ReleaseBlockerCategory.UNSUPPORTED_CLAIM,
                    "consciousness claim in a release doc")
    fixture = gate.add(ReleaseBlockerCategory.FIXTURE_DEMO,
                      "fixture demo did not pass reproducibility")
    docs = gate.add(ReleaseBlockerCategory.DOCS_UNUSABLE,
                   "a doc is unclear (non-critical)")

    print("tester release blocker demo")
    print(f"  initial: release_candidate_allowed="
          f"{gate.release_candidate_allowed} open={len(gate.open_blockers)}")
    print(f"  missing-membrane critical: {membrane.critical}")
    print(f"  unsupported-claim critical: {claim.critical}")
    print(f"  fixture-demo critical: {fixture.critical}")

    waived = docs.waive("reviewed; docs will be clarified post-RC")
    print(f"  waive non-critical docs blocker: {waived}")
    blocked = claim.waive("trying to waive a critical blocker")
    print(f"  attempt to waive critical claim blocker: {blocked} "
          "(critical cannot be silently waived)")
    print(f"  final: release_candidate_allowed="
          f"{gate.release_candidate_allowed} open={len(gate.open_blockers)}")
    print("note: open release blockers prevent a tester release candidate; "
          "critical safety blockers cannot be silently waived.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
