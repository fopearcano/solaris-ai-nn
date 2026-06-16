#!/usr/bin/env python3
"""Baseline registry demo: parent, candidate, blocked, validated-with-warnings.

    python examples/run_baseline_registry_demo.py --state-dir .solaris_ai_nn_post_merge/test_registry

Registers a parent baseline and several candidate baselines (validated, blocked,
and validated-with-warnings) to show the append-only registry. Blocked baselines
remain visible and are never deleted.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.post_merge_assimilation import (
    BaselineRecord,
    BaselineRegistry,
    BaselineStatus,
)


def main():
    parser = argparse.ArgumentParser(description="Baseline registry demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_post_merge/test_registry")
    args = parser.parse_args()

    reg = BaselineRegistry(state_dir=args.state_dir)
    reg.register(BaselineRecord(baseline_id="baseline_000",
                                status=BaselineStatus.VALIDATED))
    reg.register(BaselineRecord(baseline_id="baseline_001",
                                parent_baseline_id="baseline_000",
                                status=BaselineStatus.VALIDATED))
    blocked = BaselineRecord(baseline_id="baseline_002",
                             parent_baseline_id="baseline_001",
                             status=BaselineStatus.BLOCKED_BY_SAFETY,
                             unresolved_blockers=["critical_safety_regression"])
    reg.register(blocked)
    warned = BaselineRecord(baseline_id="baseline_003",
                            parent_baseline_id="baseline_001",
                            status=BaselineStatus.VALIDATED_WITH_WARNINGS,
                            known_risks=["one inconclusive metric"])
    reg.register(warned)
    # A status update appends history rather than overwriting.
    reg.update_status("baseline_003", BaselineStatus.REGRESSION_WATCH,
                      reason="a later metric drifted")

    status = reg.status()
    print("=== Baseline registry demo ===")
    print(f"baselines registered  : {status['baseline_record_count']}")
    print(f"  validated           : {status['validated_baseline_count']}")
    print(f"  blocked             : {status['blocked_baseline_count']}")
    print(f"  candidate           : {status['candidate_baseline_count']}")
    print(f"blocked still visible : "
          f"{reg.get('baseline_002').status} "
          f"(blocked={reg.get('baseline_002').blocked})")
    print(f"append-only history   : baseline_003 has "
          f"{len(reg.get('baseline_003').status_history)} status entries")
    print(f"registry path         : {status['registry_path']}")
    print("note                  : the registry is append-only; failed/blocked "
          "baselines remain visible and are never deleted.")


if __name__ == "__main__":
    main()
