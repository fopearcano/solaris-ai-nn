#!/usr/bin/env python3
"""Repro bundle demo: snapshot manifest -> bundle manifest -> missing warning.

    python examples/run_repro_bundle_demo.py --state-dir .solaris_ai_nn_research_baseline/test_repro_bundle

Indexes a snapshot manifest (with one missing artifact) and builds a
reproducibility-bundle manifest + README. The bundle is local documentation/index
only: it installs nothing, runs nothing, and fetches nothing.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.research_baseline import (
    ReproBundleBuilder,
    ResearchSnapshotManifest,
)


def main():
    parser = argparse.ArgumentParser(description="Repro bundle demo")
    parser.add_argument(
        "--state-dir", type=str,
        default=".solaris_ai_nn_research_baseline/test_repro_bundle")
    args = parser.parse_args()

    snap = ResearchSnapshotManifest()
    snap.index("post_merge_assimilation_report", payload={"x": 1})
    snap.index("evaluation_report", payload={"y": 2})
    # replication_report intentionally not supplied -> missing (visible).
    snapshot = snap.to_dict()

    builder = ReproBundleBuilder()
    bundle = builder.build(baseline_version_id="research_baseline_v1",
                           snapshot=snapshot,
                           known_warnings=["replication report not indexed"],
                           state_dir=args.state_dir)
    paths = builder.write(bundle, args.state_dir)
    integrity = bundle.integrity()

    print("=== Repro bundle demo ===")
    print(f"indexed artifacts     : {snapshot['snapshot_artifact_count']}")
    print(f"missing artifacts     : {snapshot['missing_snapshot_artifact_count']}"
          f" (e.g. {snapshot['missing'][:3]})")
    print(f"required commands     : {bundle.required_commands}")
    print(f"example commands      : {len(bundle.example_commands)}")
    print(f"installs deps         : {bundle.to_dict()['installs_dependencies']}")
    print(f"runs commands         : {bundle.to_dict()['runs_commands']}")
    print(f"fetches remote        : {bundle.to_dict()['fetches_remote']}")
    print(f"bundle integrity ok   : {integrity.ok} "
          f"(missing {len(integrity.missing_artifacts)})")
    print(f"manifest              : {paths['manifest']}")
    print(f"README                : {paths['readme']}")
    print("note                  : the reproducibility bundle is local "
          "documentation/index only; it installs nothing, runs nothing, and "
          "fetches no remote resource.")


if __name__ == "__main__":
    main()
