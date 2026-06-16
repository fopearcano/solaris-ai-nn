#!/usr/bin/env python3
"""Limitation registry demo: warning, major, and critical (blocks validation).

    python examples/run_limitation_registry_demo.py --state-dir .solaris_ai_nn_research_baseline/test_limitation_registry

Builds a limitation registry with a warning, a major, and a critical limitation.
A critical limitation blocks validated status; limitations are kept
operator-visible, never buried in prose.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.research_baseline import (
    BaselineLimitationRegistry,
    LimitationCategory,
    LimitationSeverity,
)


def main():
    parser = argparse.ArgumentParser(description="Limitation registry demo")
    parser.add_argument(
        "--state-dir", type=str,
        default=".solaris_ai_nn_research_baseline/test_limitation_registry")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    reg = BaselineLimitationRegistry()
    reg.add(LimitationCategory.INSUFFICIENT_REPLICATION,
            LimitationSeverity.WARNING,
            detail="only two runs registered",
            evidence_refs=["replication:matrix"])
    reg.add(LimitationCategory.MISSING_LIVE_DATA, LimitationSeverity.MAJOR,
            detail="no live read-only evidence yet",
            evidence_refs=["snapshot:live_field"])
    reg.add(LimitationCategory.WEAK_SAFETY_EVIDENCE, LimitationSeverity.CRITICAL,
            detail="safety invariant evidence missing",
            evidence_refs=["validation:safety_invariants"])
    d = reg.to_dict()

    print("=== Limitation registry demo ===")
    print(f"limitations           : {d['limitation_count']}")
    for l in d["limitations"]:
        print(f"  [{l['severity']:8s}] {l['category']}: {l['detail']}")
    print(f"critical limitations  : {d['critical_limitation_count']}")
    print(f"blocks validation     : {d['blocks_validation']}")
    print("note                  : a critical limitation blocks validated "
          "status; limitations are part of the baseline and kept "
          "operator-visible, never buried in prose.")


if __name__ == "__main__":
    main()
