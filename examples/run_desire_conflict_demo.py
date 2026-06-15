#!/usr/bin/env python3
"""Desire conflict demo: novelty vs stability, inspect vs consolidate, LOGOS.

    python examples/run_desire_conflict_demo.py --state-dir .solaris_ai_nn_desire/test_desire_conflict

Builds competing desire candidates by hand and shows the conflict detector surfacing
novelty-vs-stability and inspect-vs-consolidate conflicts that feed LOGOS tensions.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.desire_formation import (
    ConflictDetector,
    DesireCandidate,
    DesireKind,
)


def main():
    parser = argparse.ArgumentParser(description="Desire conflict demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_desire/test_desire_conflict")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    desires = [
        DesireCandidate(kind=DesireKind.FOCUS_MODALITY),
        DesireCandidate(kind=DesireKind.STABILIZE_CONCEPT),
        DesireCandidate(kind=DesireKind.INSPECT_ABSENCE),
        DesireCandidate(kind=DesireKind.CONSOLIDATE_MEMORY),
    ]
    detector = ConflictDetector()
    conflicts = detector.detect(desires)

    print("=== Desire conflict demo ===")
    print(f"desire candidates     : {[d.kind for d in desires]}")
    print(f"conflicts detected    : {len(conflicts)}")
    for c in conflicts:
        print(f"  {c.conflict_type:36s} refs={c.desire_refs}")
    # A safety conflict can also be recorded explicitly.
    detector.add_safety_conflict(desires[0].desire_id)
    print(f"after safety conflict : {len(detector.conflicts)}")
    print("note: desire conflicts feed LOGOS, may inhibit or defer desires, and "
          "are never hidden; ambiguous tensions are not resolved prematurely.")


if __name__ == "__main__":
    main()
