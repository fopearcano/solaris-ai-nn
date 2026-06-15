#!/usr/bin/env python3
"""Architecture snapshot demo: snapshot + diff between two snapshots.

    python examples/run_architecture_snapshot_demo.py --state-dir .solaris_ai_nn_architecture/test_snapshot

Builds an architecture snapshot, then a second snapshot after a lifecycle change,
and diffs them. Snapshots are versioned records; they change nothing.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.architecture_evolution import (
    ArchitectureSnapshotBuilder,
    ModuleInventory,
)


def main():
    parser = argparse.ArgumentParser(description="Architecture snapshot demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_architecture/test_snapshot")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    inv = ModuleInventory()
    sb = ArchitectureSnapshotBuilder(base_dir=args.state_dir)

    snap1 = sb.build(inventory=inv,
                     lifecycle_assessments={"latent": {"lifecycle_class":
                                                       "experimental_keep"}})
    sb.write(snap1)
    # A second snapshot after a (mock) lifecycle change.
    snap2 = sb.build(inventory=inv,
                     lifecycle_assessments={"latent": {"lifecycle_class":
                                                       "candidate_for_pruning"}})
    paths = sb.write(snap2)
    diff = sb.diff(snap1, snap2)

    print("=== Architecture snapshot demo ===")
    print(f"snapshot 1 id         : {snap1.snapshot_id}")
    print(f"snapshot 2 id         : {snap2.snapshot_id}")
    print(f"module status changes : {diff.module_status_changes}")
    print(f"roadmap changed       : {diff.roadmap_changed}")
    print(f"latest snapshot       : {paths['latest']}")
    print("note                  : snapshots are versioned records; they "
          "change nothing.")


if __name__ == "__main__":
    main()
